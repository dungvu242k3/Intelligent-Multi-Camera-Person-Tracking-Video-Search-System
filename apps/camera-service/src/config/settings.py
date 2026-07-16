import os
from pydantic_settings import BaseSettings

class CameraServiceSettings(BaseSettings):
    """Configuration settings for the Camera microservice."""
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql+asyncpg://mcpt_user:change_me_in_production@localhost:5432/mcpt_db"
    )
    SERVICE_NAME: str = "camera-service"
    HEALTH_CHECK_INTERVAL_SECONDS: int = 15 # Period to probe RTSP feeds

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = CameraServiceSettings()
