"""
AI Pipeline Service entry point.
Initialises all components and starts the DeepStream GStreamer pipeline.
"""
import argparse
import logging
import os
import sys
import signal

# ---- Monorepo PYTHONPATH ----
sys.path.insert(0, "/app")
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from pipelines.deepstream_pipeline import DeepStreamPipeline
from plugins.probe_callbacks import DeepStreamProbeCallbacks
from events.kafka_producer import KafkaEventProducer
from storage.crop_saver import CropSaver
from storage.minio_client import MinioStorageClient
from reid.mtmc_association import MTMCAssociator, PersonGallery
from reid.gallery_manager import PersonGalleryManager
from utils.gpu_monitor import GpuMonitor

# ---- Structured logger ----
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("ai_service")

# ---- Global references for signal handler ----
pipeline_instance = None
crop_saver_instance = None
kafka_producer_instance = None
gpu_monitor_instance = None


def signal_handler(sig, frame):
    """Graceful shutdown handler."""
    logger.info("Received termination signal. Shutting down...")

    global pipeline_instance, crop_saver_instance, kafka_producer_instance, gpu_monitor_instance

    if pipeline_instance:
        try:
            pipeline_instance.stop()
        except Exception as e:
            logger.error(f"Error stopping pipeline: {e}")

    if crop_saver_instance:
        logger.info("Waiting for pending MinIO uploads to complete...")
        try:
            crop_saver_instance.shutdown()
        except Exception as e:
            logger.error(f"Error shutting down CropSaver: {e}")

    if kafka_producer_instance:
        logger.info("Flushing Kafka producer queue...")
        try:
            kafka_producer_instance.flush(timeout=3.0)
        except Exception as e:
            logger.error(f"Error flushing Kafka: {e}")

    if gpu_monitor_instance:
        gpu_monitor_instance.stop()

    logger.info("Graceful shutdown complete.")
    sys.exit(0)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Multi-Camera AI Pipeline (DeepStream)")

    parser.add_argument(
        "--source", action="append", required=True,
        help="RTSP URL or file:// path (repeatable for multiple cameras)"
    )
    parser.add_argument(
        "--pgie-config",
        default=os.getenv("PGIE_CONFIG", "apps/ai-service/configs/pgie_yolov8.txt"),
        help="Primary GIE (YOLO detector) config path"
    )
    parser.add_argument(
        "--sgie-config",
        default=os.getenv("SGIE_CONFIG", "apps/ai-service/configs/sgie_reid.txt"),
        help="Secondary GIE (ReID extractor) config path"
    )
    parser.add_argument(
        "--tracker-config",
        default=os.getenv("TRACKER_CONFIG", "apps/ai-service/configs/tracker_config.yml"),
        help="NvDCF tracker config path"
    )
    parser.add_argument(
        "--kafka-broker",
        default=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
    )
    parser.add_argument(
        "--kafka-topic", default=os.getenv("KAFKA_DETECTION_TOPIC", "detection-events"),
    )
    parser.add_argument(
        "--minio-endpoint", default=os.getenv("MINIO_ENDPOINT", "minio:9000"),
    )
    parser.add_argument(
        "--minio-access-key", default=os.getenv("MINIO_ROOT_USER", "minioadmin"),
    )
    parser.add_argument(
        "--minio-secret-key", default=os.getenv("MINIO_ROOT_PASSWORD", "minioadmin"),
    )
    parser.add_argument("--minio-secure", action="store_true")
    parser.add_argument(
        "--qdrant-host", default=os.getenv("QDRANT_HOST", "qdrant"),
    )
    parser.add_argument(
        "--qdrant-port", type=int, default=int(os.getenv("QDRANT_PORT", "6333")),
    )
    parser.add_argument(
        "--gpu-id", type=int, default=0, help="CUDA GPU device index"
    )
    parser.add_argument(
        "--reid-threshold", type=float,
        default=float(os.getenv("REID_MATCH_THRESHOLD", "0.75")),
        help="Cosine similarity threshold for cross-camera re-identification"
    )

    return parser.parse_args()


def main():
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    args = parse_args()

    logger.info("=== Intelligent Multi-Camera Tracking Pipeline ===")
    logger.info(f"Sources ({len(args.source)}): {args.source}")
    logger.info(f"PGIE config : {args.pgie_config}")
    logger.info(f"SGIE config : {args.sgie_config}")
    logger.info(f"Tracker cfg : {args.tracker_config}")
    logger.info(f"Kafka broker: {args.kafka_broker} → topic: {args.kafka_topic}")
    logger.info(f"MinIO       : {args.minio_endpoint}")
    logger.info(f"Qdrant      : {args.qdrant_host}:{args.qdrant_port}")
    logger.info(f"ReID threshold: {args.reid_threshold}")

    global pipeline_instance, crop_saver_instance, kafka_producer_instance, gpu_monitor_instance

    try:
        # ── 1. GPU monitor (daemon thread) ──────────────────────────────
        gpu_monitor_instance = GpuMonitor(gpu_index=args.gpu_id, poll_interval_s=5.0)
        gpu_monitor_instance.start()

        # ── 2. Kafka producer ────────────────────────────────────────────
        kafka_producer_instance = KafkaEventProducer(
            bootstrap_servers=args.kafka_broker,
            client_id="deepstream-ai-service",
        )

        # ── 3. MinIO + CropSaver ────────────────────────────────────────
        minio_client = MinioStorageClient(
            endpoint=args.minio_endpoint,
            access_key=args.minio_access_key,
            secret_key=args.minio_secret_key,
            secure=args.minio_secure,
        )
        crop_saver_instance = CropSaver(
            minio_client=minio_client,
            bucket_name="detection-crops",
            max_workers=4,
        )

        # ── 4. MTMC ReID associator ────────────────────────────────────
        gallery = PersonGallery(match_threshold=args.reid_threshold)
        mtmc_associator = MTMCAssociator(gallery=gallery)

        # ── 5. Qdrant gallery manager (optional — graceful degradation) ─
        gallery_manager = PersonGalleryManager(
            host=args.qdrant_host,
            port=args.qdrant_port,
        )

        # ── 6. Probe callbacks ─────────────────────────────────────────
        callbacks = DeepStreamProbeCallbacks(
            kafka_producer=kafka_producer_instance,
            crop_saver=crop_saver_instance,
            kafka_topic=args.kafka_topic,
            mtmc_associator=mtmc_associator,
            gallery_manager=gallery_manager,
        )

        # ── 7. Build & start DeepStream pipeline ───────────────────────
        pipeline_instance = DeepStreamPipeline(
            sources=args.source,
            pgie_config=args.pgie_config,
            sgie_config=args.sgie_config,
            tracker_config=args.tracker_config,
            callbacks=callbacks,
        )

        # Blocks on GLib.MainLoop until stop() is called
        pipeline_instance.start()

    except Exception as e:
        logger.critical(f"Fatal error during pipeline execution: {e}", exc_info=True)
        signal_handler(None, None)


if __name__ == "__main__":
    main()
