import os
from pydantic import model_validator
from pydantic_settings import BaseSettings

class NotificationSettings(BaseSettings):
    """Configuration settings for the Notification service."""
    KAFKA_BOOTSTRAP_SERVERS: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:29092")
    KAFKA_TOPIC_ALERTS: str = "alert-events"
    KAFKA_GROUP_ID: str = "notification-service-group"
    
    GATEWAY_ALERTS_URL: str = os.getenv("GATEWAY_ALERTS_URL", "http://gateway:8000/api/v1/alerts/publish")
    INTERNAL_SERVICE_KEY: str = os.getenv("INTERNAL_SERVICE_KEY", "")
    SERVICE_NAME: str = "notification-service"
    ENV: str = os.getenv("ENV", "development")

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

settings = NotificationSettings()
