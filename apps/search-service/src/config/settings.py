import os
from pydantic_settings import BaseSettings

class SearchServiceSettings(BaseSettings):
    """Configuration settings for the Search microservice."""
    SERVICE_NAME: str = "search-service"
    QDRANT_HOST: str = os.getenv("QDRANT_HOST", "localhost")
    QDRANT_PORT: int = int(os.getenv("QDRANT_PORT", "6333"))

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = SearchServiceSettings()
