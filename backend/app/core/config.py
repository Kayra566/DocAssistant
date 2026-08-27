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

    # Auth / JWT
    JWT_SECRET: str = "change-me-in-production-please-32bytes-min"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    EMAIL_VERIFICATION_EXPIRE_HOURS: int = 24
    PASSWORD_RESET_EXPIRE_HOURS: int = 1

    # Account lockout
    MAX_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_MINUTES: int = 15

    # Dev: email gönderimi henüz yok (Faz 7). Local'de token'ları API yanıtında döndür.
    EXPOSE_DEV_TOKENS: bool = True

    # Object storage (MinIO local / S3 prod)
    STORAGE_BACKEND: Literal["local", "s3"] = "local"
    STORAGE_LOCAL_DIR: str = "./_storage"
    S3_ENDPOINT: str = "http://localhost:9000"
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin"
    S3_BUCKET: str = "docassistant"
    S3_REGION: str = "us-east-1"

    # Doküman yükleme
    MAX_UPLOAD_SIZE_MB: int = 25
    SIGNED_URL_EXPIRE_MINUTES: int = 60
    # Yükleme sonrası işlemeyi Celery yerine inline (await) yap — local/test için pratik.
    PROCESS_DOCUMENTS_EAGER: bool = True
    ENABLE_OCR: bool = False
    # Embedding boyutu (hashing embedder için).
    EMBEDDING_DIM: int = 384
    EMBEDDING_PROVIDER: Literal["hashing", "sentence_transformers"] = "hashing"

    # Plan bazlı doküman kotası (Faz 5'te Stripe ile genişleyecek)
    QUOTA_FREE_DOCUMENTS: int = 10
    QUOTA_PRO_DOCUMENTS: int = 100
    QUOTA_BUSINESS_DOCUMENTS: int = 100000

    # LLM
    LLM_PROVIDER: Literal["ollama", "openai", "fake"] = "fake"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.1:8b"
    LLM_TIMEOUT_SECONDS: int = 60
    RAG_TOP_K: int = 5

    # AI kotası (aylık token bütçesi, plan bazlı)
    QUOTA_FREE_AI_TOKENS: int = 100_000
    QUOTA_PRO_AI_TOKENS: int = 2_000_000
    QUOTA_BUSINESS_AI_TOKENS: int = 20_000_000

    # AI sonuç önbelleği
    AI_CACHE_BACKEND: Literal["memory", "redis"] = "memory"
    AI_CACHE_TTL_SECONDS: int = 86400

    # AI görevleri (summary/quiz/translate...)
    # Eager modda iş Celery yerine inline (await) çalışır — local/test için pratik.
    AI_JOBS_EAGER: bool = True
    # Bir göreve verilecek maksimum bağlam uzunluğu (karakter).
    AI_TASK_CONTEXT_CHARS: int = 12000
    AI_QUIZ_MAX_QUESTIONS: int = 20

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
