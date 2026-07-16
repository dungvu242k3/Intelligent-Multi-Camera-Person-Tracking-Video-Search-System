import os
from pydantic import model_validator
from pydantic_settings import BaseSettings

WEAK_SECRET_VALUES = {
    "",
    "change_this_to_a_secure_256_bit_key_in_production_environment_12345",
}

DEVELOPMENT_JWT_SECRET = "local-development-only-jwt-secret-use-env-for-shared-services-32-bytes"

class AuthServiceSettings(BaseSettings):
    """Configuration settings for the Authentication microservice."""
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql+asyncpg://mcpt_user:change_me_in_production@localhost:5432/mcpt_db"
    )
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    DB_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", "10"))
    DB_MAX_OVERFLOW: int = int(os.getenv("DB_MAX_OVERFLOW", "5"))
    DB_POOL_TIMEOUT_SECONDS: int = int(os.getenv("DB_POOL_TIMEOUT_SECONDS", "30"))
    DB_POOL_RECYCLE_SECONDS: int = int(os.getenv("DB_POOL_RECYCLE_SECONDS", "1800"))
    SERVICE_NAME: str = "auth-service"
    ENV: str = os.getenv("ENV", "development")

    @model_validator(mode="after")
    def validate_secrets(self):
        if not self.JWT_SECRET_KEY:
            self.JWT_SECRET_KEY = DEVELOPMENT_JWT_SECRET

        is_prod = self.ENV.lower() == "production"
        if is_prod and (
            self.JWT_SECRET_KEY in WEAK_SECRET_VALUES or len(self.JWT_SECRET_KEY) < 32
        ):
            raise ValueError("JWT_SECRET_KEY must be set to a strong production secret")
        return self

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = AuthServiceSettings()
