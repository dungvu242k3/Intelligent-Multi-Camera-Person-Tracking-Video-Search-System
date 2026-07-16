import os
from pydantic_settings import BaseSettings

class SchedulerSettings(BaseSettings):
    """Configuration settings for the Scheduler service."""
    CLEANUP_INTERVAL_HOURS: int = int(os.getenv("CLEANUP_INTERVAL_HOURS", "24"))
    RETENTION_DAYS: int = int(os.getenv("RETENTION_DAYS", "30"))
    
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://mcpt_user:change_me_in_production@localhost:5432/mcpt_db"
    )
    
    QDRANT_HOST: str = os.getenv("QDRANT_HOST", "qdrant")
    QDRANT_PORT: int = int(os.getenv("QDRANT_PORT", "6333"))
    QDRANT_COLLECTION_REID: str = "person_embeddings"
    
    MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT", "minio:9000")
    MINIO_ACCESS_KEY: str = os.getenv("MINIO_ROOT_USER", "minioadmin")
    MINIO_SECRET_KEY: str = os.getenv("MINIO_ROOT_PASSWORD", "minioadmin")
    MINIO_BUCKET_CROPS: str = "person-crops"
    
    SERVICE_NAME: str = "scheduler-service"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = SchedulerSettings()
