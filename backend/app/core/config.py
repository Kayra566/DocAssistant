from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # App
    APP_NAME: str = "DocAssistant"
    ENVIRONMENT: Literal["local", "staging", "production"] = "local"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # CORS (comma-separated origins)
    CORS_ORIGINS: str = "http://localhost:5173"

    # Database
    DATABASE_URL: str = (
        "postgresql+asyncpg://dev:dev@localhost:5432/docassistant"
    )

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Object storage (MinIO local / S3 prod)
    S3_ENDPOINT: str = "http://localhost:9000"
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin"
    S3_BUCKET: str = "docassistant"
    S3_REGION: str = "us-east-1"

    # LLM
    LLM_PROVIDER: Literal["ollama", "openai"] = "ollama"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.1:8b"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
