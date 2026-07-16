import os
from pydantic import model_validator
from pydantic_settings import BaseSettings

WEAK_SECRET_VALUES = {
    "",
    "change_this_to_a_secure_256_bit_key_in_production_environment_12345",
    "change_this_internal_key_in_production",
}

DEVELOPMENT_JWT_SECRET = "local-development-only-jwt-secret-use-env-for-shared-services-32-bytes"
DEVELOPMENT_INTERNAL_SERVICE_KEY = "local-development-only-internal-service-key-32-bytes"

class GatewaySettings(BaseSettings):
    """Configuration settings for the API Gateway."""
    AUTH_SERVICE_URL: str = os.getenv("AUTH_SERVICE_URL", "http://localhost:8004")
    CAMERA_SERVICE_URL: str = os.getenv("CAMERA_SERVICE_URL", "http://localhost:8002")
    SEARCH_SERVICE_URL: str = os.getenv("SEARCH_SERVICE_URL", "http://localhost:8003")
    ANALYTICS_SERVICE_URL: str = os.getenv("ANALYTICS_SERVICE_URL", "http://localhost:8001")
    NOTIFICATION_SERVICE_URL: str = os.getenv("NOTIFICATION_SERVICE_URL", "http://localhost:8005")
    
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "")
    JWT_ALGORITHM: str = "HS256"
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_REQUESTS_PER_MINUTE", "60"))
    RATE_LIMIT_ENABLED: bool = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
    SERVICE_NAME: str = "api-gateway"
    
    # Internal service-to-service authentication key
    INTERNAL_SERVICE_KEY: str = os.getenv("INTERNAL_SERVICE_KEY", "")
    ENV: str = os.getenv("ENV", "development")

    @model_validator(mode="after")
    def validate_secrets(self):
        if not self.JWT_SECRET_KEY:
            self.JWT_SECRET_KEY = DEVELOPMENT_JWT_SECRET
        if not self.INTERNAL_SERVICE_KEY:
            self.INTERNAL_SERVICE_KEY = DEVELOPMENT_INTERNAL_SERVICE_KEY

        is_prod = self.ENV.lower() == "production"
        if is_prod:
            if self.JWT_SECRET_KEY in WEAK_SECRET_VALUES or len(self.JWT_SECRET_KEY) < 32:
                raise ValueError("JWT_SECRET_KEY must be set to a strong production secret")
            if (
                self.INTERNAL_SERVICE_KEY in WEAK_SECRET_VALUES
                or len(self.INTERNAL_SERVICE_KEY) < 32
            ):
                raise ValueError("INTERNAL_SERVICE_KEY must be set to a strong production secret")
        return self

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = GatewaySettings()
