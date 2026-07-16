#!/usr/bin/env python3
"""
Qdrant Collection Initialization Script
Multi-Camera Person Tracking System

Creates the required vector collections for person re-identification
embeddings if they do not already exist.

Runs as a one-shot Docker service after qdrant is healthy.
"""

import os
import sys
import time
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [qdrant-init] %(message)s")
logger = logging.getLogger(__name__)

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import (
        Distance,
        VectorParams,
        HnswConfigDiff,
        OptimizersConfigDiff,
        QuantizationConfig,
        ScalarQuantization,
        ScalarQuantizationConfig,
        ScalarType,
    )
except ImportError:
    logger.error("qdrant-client is not installed. Run: pip install qdrant-client")
    sys.exit(1)


QDRANT_HOST = os.getenv("QDRANT_HOST", "qdrant")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
QDRANT_GRPC_PORT = int(os.getenv("QDRANT_GRPC_PORT", "6334"))

# Collection configuration
COLLECTIONS = [
    {
        "name": "person_embeddings",
        "vector_size": 512,          # OSNet x1.0 / ResNet50 Re-ID embedding dim
        "distance": Distance.COSINE,
        "description": "Person re-identification embeddings from AI pipeline",
        "hnsw_m": 16,
        "hnsw_ef_construct": 200,
        "on_disk": False,            # Set True in low-RAM production environments
    },
    {
        "name": "face_embeddings",
        "vector_size": 128,          # FaceNet / ArcFace embedding dim
        "distance": Distance.COSINE,
        "description": "Face recognition embeddings (optional module)",
        "hnsw_m": 16,
        "hnsw_ef_construct": 100,
        "on_disk": False,
    },
]

MAX_RETRIES = 15
RETRY_DELAY = 5


def wait_for_qdrant(client: QdrantClient) -> None:
    """Polls Qdrant until it responds to a health check."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            client.get_collections()
            logger.info("Qdrant is ready.")
            return
        except Exception as exc:
            logger.warning(
                "Qdrant not ready (attempt %d/%d): %s. Retrying in %ds...",
                attempt, MAX_RETRIES, exc, RETRY_DELAY,
            )
            time.sleep(RETRY_DELAY)
    logger.error("Qdrant did not become ready after %d attempts. Exiting.", MAX_RETRIES)
    sys.exit(1)


def create_collection_if_missing(client: QdrantClient, cfg: dict) -> None:
    """Creates a Qdrant collection idempotently."""
    name = cfg["name"]
    existing = {c.name for c in client.get_collections().collections}

    if name in existing:
        logger.info("Collection '%s' already exists. Skipping.", name)
        return

    logger.info("Creating collection '%s' (dim=%d, distance=%s)...", name, cfg["vector_size"], cfg["distance"])
    client.create_collection(
        collection_name=name,
        vectors_config=VectorParams(
            size=cfg["vector_size"],
            distance=cfg["distance"],
            on_disk=cfg.get("on_disk", False),
        ),
        hnsw_config=HnswConfigDiff(
            m=cfg.get("hnsw_m", 16),
            ef_construct=cfg.get("hnsw_ef_construct", 200),
            full_scan_threshold=10_000,
            on_disk=False,
        ),
        optimizers_config=OptimizersConfigDiff(
            deleted_threshold=0.2,
            vacuum_min_vector_number=1000,
            default_segment_number=2,
        ),
        # Scalar quantization reduces memory 4x with <1% accuracy drop
        quantization_config=QuantizationConfig(
            scalar=ScalarQuantization(
                scalar=ScalarQuantizationConfig(
                    type=ScalarType.INT8,
                    quantile=0.99,
                    always_ram=True,
                )
            )
        ),
    )
    logger.info("Collection '%s' created successfully.", name)


def main() -> None:
    logger.info("Connecting to Qdrant at %s:%d...", QDRANT_HOST, QDRANT_PORT)
    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT, timeout=30)

    wait_for_qdrant(client)

    for collection_cfg in COLLECTIONS:
        create_collection_if_missing(client, collection_cfg)

    logger.info("Qdrant initialization complete. Collections:")
    for col in client.get_collections().collections:
        info = client.get_collection(col.name)
        logger.info("  - %s: %d vectors", col.name, info.vectors_count or 0)


if __name__ == "__main__":
    main()
