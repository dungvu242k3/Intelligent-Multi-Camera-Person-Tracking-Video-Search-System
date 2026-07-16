import os
from pydantic_settings import BaseSettings

class NotificationSettings(BaseSettings):
    """Configuration settings for the Notification service."""
    KAFKA_BOOTSTRAP_SERVERS: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:29092")
    KAFKA_TOPIC_ALERTS: str = "alert-events"
    KAFKA_GROUP_ID: str = "notification-service-group"
    
    GATEWAY_ALERTS_URL: str = os.getenv("GATEWAY_ALERTS_URL", "http://gateway:8000/api/v1/alerts/publish")
    SERVICE_NAME: str = "notification-service"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = NotificationSettings()
