import os

from src.pipelines.pipeline_config import PipelineConfig


def test_pipeline_config_default_values() -> None:
    """Verifies that PipelineConfig instantiates with correct default values."""
    config = PipelineConfig()
    assert config.kafka_broker == "kafka:9092"
    assert config.kafka_topic == "detection-events"
    assert config.minio_endpoint == "minio:9000"
    assert config.minio_access_key == "minioadmin"
    assert config.minio_secret_key == "minioadmin"
    assert config.minio_secure is False
    assert config.minio_bucket == "detection-crops"
    assert config.qdrant_host == "qdrant"
    assert config.qdrant_port == 6333
    assert config.reid_threshold == 0.75
    assert config.embedding_dim == 512
    assert config.mux_width == 1920
    assert config.mux_height == 1080
    assert config.batch_push_timeout_us == 40000
    assert config.crop_saver_workers == 4


def test_pipeline_config_from_env() -> None:
    """Verifies that PipelineConfig loads properties correctly from environment variables."""
    # Set environment variables
    os.environ["KAFKA_BOOTSTRAP_SERVERS"] = "test-kafka:9092"
    os.environ["KAFKA_DETECTION_TOPIC"] = "test-topic"
    os.environ["MINIO_ENDPOINT"] = "test-minio:9000"
    os.environ["MINIO_ROOT_USER"] = "test-user"
    os.environ["MINIO_ROOT_PASSWORD"] = "test-password"
    os.environ["QDRANT_HOST"] = "test-qdrant"
    os.environ["QDRANT_PORT"] = "16333"
    os.environ["REID_MATCH_THRESHOLD"] = "0.85"
    os.environ["PGIE_CONFIG"] = "/custom/pgie.txt"
    os.environ["SGIE_CONFIG"] = "/custom/sgie.txt"
    os.environ["TRACKER_CONFIG"] = "/custom/tracker.yml"

    try:
        config = PipelineConfig.from_env()
        assert config.kafka_broker == "test-kafka:9092"
        assert config.kafka_topic == "test-topic"
        assert config.minio_endpoint == "test-minio:9000"
        assert config.minio_access_key == "test-user"
        assert config.minio_secret_key == "test-password"
        assert config.qdrant_host == "test-qdrant"
        assert config.qdrant_port == 16333
        assert config.reid_threshold == 0.85
        assert config.pgie_config == "/custom/pgie.txt"
        assert config.sgie_config == "/custom/sgie.txt"
        assert config.tracker_config == "/custom/tracker.yml"
    finally:
        # Clean up env
        for var in [
            "KAFKA_BOOTSTRAP_SERVERS", "KAFKA_DETECTION_TOPIC", "MINIO_ENDPOINT",
            "MINIO_ROOT_USER", "MINIO_ROOT_PASSWORD", "QDRANT_HOST", "QDRANT_PORT",
            "REID_MATCH_THRESHOLD", "PGIE_CONFIG", "SGIE_CONFIG", "TRACKER_CONFIG"
        ]:
            os.environ.pop(var, None)
BlockOutput = ""
