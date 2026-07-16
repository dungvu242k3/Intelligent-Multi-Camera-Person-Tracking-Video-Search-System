import os
from pydantic_settings import BaseSettings

class GatewaySettings(BaseSettings):
    """Configuration settings for the API Gateway."""
    AUTH_SERVICE_URL: str = os.getenv("AUTH_SERVICE_URL", "http://localhost:8004")
    CAMERA_SERVICE_URL: str = os.getenv("CAMERA_SERVICE_URL", "http://localhost:8002")
    SEARCH_SERVICE_URL: str = os.getenv("SEARCH_SERVICE_URL", "http://localhost:8003")
    ANALYTICS_SERVICE_URL: str = os.getenv("ANALYTICS_SERVICE_URL", "http://localhost:8001")
    NOTIFICATION_SERVICE_URL: str = os.getenv("NOTIFICATION_SERVICE_URL", "http://localhost:8005")
    
    JWT_SECRET_KEY: str = os.getenv(
        "JWT_SECRET_KEY", 
        "change_this_to_a_secure_256_bit_key_in_production_environment_12345"
    )
    JWT_ALGORITHM: str = "HS256"
    SERVICE_NAME: str = "api-gateway"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = GatewaySettings()
