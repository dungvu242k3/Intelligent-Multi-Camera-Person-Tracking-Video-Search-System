import os
from pydantic_settings import BaseSettings

class SchedulerSettings(BaseSettings):
    """Configuration settings for the Scheduler service."""
    CLEANUP_INTERVAL_HOURS: int = int(os.getenv("CLEANUP_INTERVAL_HOURS", "24"))
    RETENTION_DAYS: int = int(os.getenv("RETENTION_DAYS", "30"))
    
    QDRANT_HOST: str = os.getenv("QDRANT_HOST", "qdrant")
    QDRANT_PORT: int = int(os.getenv("QDRANT_PORT", "6333"))
    MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT", "minio:9000")
    
    SERVICE_NAME: str = "scheduler-service"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = SchedulerSettings()
