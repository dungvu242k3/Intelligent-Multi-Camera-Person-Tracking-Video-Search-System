import os
from pydantic_settings import BaseSettings

class AuthServiceSettings(BaseSettings):
    """Configuration settings for the Authentication microservice."""
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql+asyncpg://mcpt_user:change_me_in_production@localhost:5432/mcpt_db"
    )
    JWT_SECRET_KEY: str = os.getenv(
        "JWT_SECRET_KEY",
        "change_this_to_a_secure_256_bit_key_in_production_environment_12345"
    )
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    SERVICE_NAME: str = "auth-service"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = AuthServiceSettings()
