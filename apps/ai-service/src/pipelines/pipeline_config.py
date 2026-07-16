"""
Pipeline configuration dataclass — centralizes all tunable parameters
that are typically injected via CLI args or environment variables.
"""
from __future__ import annotations
import os
from dataclasses import dataclass, field
from typing import List


@dataclass
class PipelineConfig:
    """Complete configuration for the DeepStream tracking pipeline."""

    # ── Sources ─────────────────────────────────────────────
    sources: List[str] = field(default_factory=list)

    # ── Model configs ────────────────────────────────────────
    pgie_config: str = "/app/apps/ai-service/configs/pgie_yolov8.txt"
    sgie_config: str = "/app/apps/ai-service/configs/sgie_reid.txt"
    tracker_config: str = "/app/apps/ai-service/configs/tracker_config.yml"

    # ── GPU ──────────────────────────────────────────────────
    gpu_id: int = 0

    # ── Kafka ────────────────────────────────────────────────
    kafka_broker: str = "kafka:9092"
    kafka_topic: str = "detection-events"

    # ── MinIO ────────────────────────────────────────────────
    minio_endpoint: str = "minio:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_secure: bool = False
    minio_bucket: str = "detection-crops"

    # ── Qdrant ───────────────────────────────────────────────
    qdrant_host: str = "qdrant"
    qdrant_port: int = 6333

    # ── ReID ─────────────────────────────────────────────────
    reid_threshold: float = 0.75
    embedding_dim: int = 512

    # ── Stream mux ───────────────────────────────────────────
    mux_width: int = 1920
    mux_height: int = 1080
    batch_push_timeout_us: int = 40_000  # 40ms

    # ── CropSaver ────────────────────────────────────────────
    crop_saver_workers: int = 4

    @classmethod
    def from_env(cls) -> "PipelineConfig":
        """Constructs config from environment variables (docker-compose style)."""
        return cls(
            kafka_broker=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092"),
            kafka_topic=os.getenv("KAFKA_DETECTION_TOPIC", "detection-events"),
            minio_endpoint=os.getenv("MINIO_ENDPOINT", "minio:9000"),
            minio_access_key=os.getenv("MINIO_ROOT_USER", "minioadmin"),
            minio_secret_key=os.getenv("MINIO_ROOT_PASSWORD", "minioadmin"),
            qdrant_host=os.getenv("QDRANT_HOST", "qdrant"),
            qdrant_port=int(os.getenv("QDRANT_PORT", "6333")),
            reid_threshold=float(os.getenv("REID_MATCH_THRESHOLD", "0.75")),
            pgie_config=os.getenv("PGIE_CONFIG", "/app/apps/ai-service/configs/pgie_yolov8.txt"),
            sgie_config=os.getenv("SGIE_CONFIG", "/app/apps/ai-service/configs/sgie_reid.txt"),
            tracker_config=os.getenv("TRACKER_CONFIG", "/app/apps/ai-service/configs/tracker_config.yml"),
        )
