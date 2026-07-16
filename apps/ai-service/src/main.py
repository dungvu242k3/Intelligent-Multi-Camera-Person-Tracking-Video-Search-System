import argparse
import logging
import os
import sys
import signal
from typing import List

# Setup path to import packages correctly in monorepo
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from pipelines.deepstream_pipeline import DeepStreamPipeline
from plugins.probe_callbacks import DeepStreamProbeCallbacks
from packages.shared.messaging.kafka import KafkaEventProducer
from packages.shared.storage.minio import MinioStorageClient
from storage.crop_saver import CropSaver

# Initialize structured logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("ai_service")

# Global pipeline reference for signal handlers
pipeline_instance = None
crop_saver_instance = None
kafka_producer_instance = None

def signal_handler(sig, frame):
    """Graceful shutdown handler for OS signals."""
    logger.info("Received termination signal. Shutting down system components...")
    
    global pipeline_instance, crop_saver_instance, kafka_producer_instance
    
    # 1. Stop GStreamer pipeline
    if pipeline_instance:
        try:
            pipeline_instance.stop()
        except Exception as e:
            logger.error(f"Error stopping GStreamer pipeline: {e}")

    # 2. Wait for async S3 crop uploads to complete
    if crop_saver_instance:
        logger.info("Waiting for pending MinIO crop uploads to complete...")
        try:
            crop_saver_instance.shutdown()
        except Exception as e:
            logger.error(f"Error shutting down CropSaver pool: {e}")

    # 3. Flush and close Kafka producer buffer
    if kafka_producer_instance:
        logger.info("Flushing Kafka producer events queue...")
        try:
            kafka_producer_instance.flush(timeout=2.0)
        except Exception as e:
            logger.error(f"Error flushing Kafka producer: {e}")

    logger.info("Graceful shutdown complete. Exiting process.")
    sys.exit(0)

def main():
    # Register termination signals
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # 1. Parse command-line args
    parser = argparse.ArgumentParser(description="Multi-Camera AI Pipeline (DeepStream)")
    parser.add_argument(
        "--source", 
        action="append", 
        required=True, 
        help="Input RTSP URLs or local File paths (can specify multiple times)"
    )
    parser.add_argument(
        "--pgie-config", 
        default="apps/ai-service/configs/pgie_yolov8.txt", 
        help="Primary GIE (YOLO detector) config file path"
    )
    parser.add_argument(
        "--sgie-config", 
        default="apps/ai-service/configs/sgie_reid.txt", 
        help="Secondary GIE (ReID) config file path"
    )
    parser.add_argument(
        "--tracker-config", 
        default="apps/ai-service/configs/tracker_config.yml", 
        help="NvDCF tracker config file path"
    )
    parser.add_argument(
        "--kafka-broker", 
        default=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"), 
        help="Kafka bootstrap server endpoint"
    )
    parser.add_argument(
        "--kafka-topic", 
        default="detection-events", 
        help="Kafka topic for publishing detection metadata"
    )
    parser.add_argument(
        "--minio-endpoint", 
        default=os.getenv("MINIO_ENDPOINT", "localhost:9000"), 
        help="MinIO server host and port"
    )
    parser.add_argument(
        "--minio-access-key", 
        default=os.getenv("MINIO_ROOT_USER", "minioadmin"), 
        help="MinIO root access key"
    )
    parser.add_argument(
        "--minio-secret-key", 
        default=os.getenv("MINIO_ROOT_PASSWORD", "minioadmin"), 
        help="MinIO root secret key"
    )
    parser.add_argument(
        "--minio-secure", 
        action="store_true", 
        help="Enable HTTPS connection for MinIO (S3)"
    )
    args = parser.parse_args()

    logger.info("Initializing Intelligent Multi-Camera Tracking Pipeline...")
    logger.info(f"Sources: {args.source}")

    global pipeline_instance, crop_saver_instance, kafka_producer_instance

    try:
        # 2. Init Kafka Producer
        kafka_producer_instance = KafkaEventProducer(
            bootstrap_servers=args.kafka_broker,
            client_id="deepstream-ai-service"
        )

        # 3. Init Minio & CropSaver
        minio_client = MinioStorageClient(
            endpoint=args.minio_endpoint,
            access_key=args.minio_access_key,
            secret_key=args.minio_secret_key,
            secure=args.minio_secure
        )
        crop_saver_instance = CropSaver(
            minio_client=minio_client,
            bucket_name="detection-crops",
            max_workers=4
        )

        # 4. Init DeepStream Probe Callbacks
        callbacks = DeepStreamProbeCallbacks(
            kafka_producer=kafka_producer_instance,
            crop_saver=crop_saver_instance,
            kafka_topic=args.kafka_topic
        )

        # 5. Build and Start the GStreamer Pipeline
        pipeline_instance = DeepStreamPipeline(
            sources=args.source,
            pgie_config=args.pgie_config,
            sgie_config=args.sgie_config,
            tracker_config=args.tracker_config,
            callbacks=callbacks
        )

        # Start blocks execution (runs GLib main loop)
        pipeline_instance.start()

    except Exception as e:
        logger.critical(f"Unhandled exception during pipeline execution: {e}", exc_info=True)
        # Force cleanup
        signal_handler(None, None)

if __name__ == "__main__":
    main()
