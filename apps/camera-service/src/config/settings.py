import os
from pydantic import model_validator
from pydantic_settings import BaseSettings

class CameraServiceSettings(BaseSettings):
    """Configuration settings for the Camera microservice."""
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql+asyncpg://mcpt_user:change_me_in_production@localhost:5432/mcpt_db"
    )
    SERVICE_NAME: str = "camera-service"
    HEALTH_CHECK_INTERVAL_SECONDS: int = 15 # Period to probe RTSP feeds
    DB_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", "10"))
    DB_MAX_OVERFLOW: int = int(os.getenv("DB_MAX_OVERFLOW", "5"))
    DB_POOL_TIMEOUT_SECONDS: int = int(os.getenv("DB_POOL_TIMEOUT_SECONDS", "30"))
    DB_POOL_RECYCLE_SECONDS: int = int(os.getenv("DB_POOL_RECYCLE_SECONDS", "1800"))
    INTERNAL_SERVICE_KEY: str = os.getenv("INTERNAL_SERVICE_KEY", "")
    ENV: str = os.getenv("ENV", "development")
    HEALTH_CHECK_MAX_CONCURRENCY: int = int(os.getenv("HEALTH_CHECK_MAX_CONCURRENCY", "20"))
    CAMERA_LIST_MAX_LIMIT: int = int(os.getenv("CAMERA_LIST_MAX_LIMIT", "100"))

    @model_validator(mode="after")
    def validate_secrets(self):
        if not self.INTERNAL_SERVICE_KEY:
            self.INTERNAL_SERVICE_KEY = "local-development-only-internal-service-key-32-bytes"
        if self.ENV.lower() == "production" and (
            len(self.INTERNAL_SERVICE_KEY) < 32
            or self.INTERNAL_SERVICE_KEY == "change_this_internal_key_in_production"
        ):
            raise ValueError("INTERNAL_SERVICE_KEY must be set to a strong production secret")
        return self

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = CameraServiceSettings()
