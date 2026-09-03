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

    # Plan bazlı depolama kotası (MB)
    QUOTA_FREE_STORAGE_MB: int = 50
    QUOTA_PRO_STORAGE_MB: int = 1024
    QUOTA_BUSINESS_STORAGE_MB: int = 10240

    # Plan bazlı aylık AI istek kotası
    QUOTA_FREE_AI_REQUESTS: int = 100
    QUOTA_PRO_AI_REQUESTS: int = 1000
    QUOTA_BUSINESS_AI_REQUESTS: int = 10000

    # Ödeme (Stripe)
    BILLING_PROVIDER: Literal["fake", "stripe"] = "fake"
    BILLING_CURRENCY: str = "USD"
    PRICE_PRO_MONTHLY: int = 19
    PRICE_BUSINESS_MONTHLY: int = 99
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_PRICE_PRO: str = "price_pro_monthly"
    STRIPE_PRICE_BUSINESS: str = "price_business_monthly"
    BILLING_SUCCESS_URL: str = "http://localhost:5173/billing?status=success"
    BILLING_CANCEL_URL: str = "http://localhost:5173/billing?status=cancel"
    BILLING_PORTAL_RETURN_URL: str = "http://localhost:5173/billing"

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

    # Paylaşım bağlantıları
    SHARE_LINK_DEFAULT_EXPIRE_HOURS: int = 168  # 7 gün
    SHARE_LINK_MAX_EXPIRE_HOURS: int = 720  # 30 gün
    # Kullanıcıya gösterilecek paylaşım adresinin ön eki.
    SHARE_PUBLIC_BASE_URL: str = "http://localhost:5173/share"

    # Export (AI sonucu → PDF/DOCX/XLSX/MD)
    # Eager modda export Celery yerine inline (await) çalışır.
    EXPORTS_EAGER: bool = True

    # Dashboard
    DASHBOARD_TREND_DAYS: int = 30
    ACTIVITY_LOG_PAGE_SIZE: int = 50

    # ---------- Faz 7: güvenlik ----------
    # Hassas alanların AES-256-GCM ile şifrelenmesi. Boşsa JWT_SECRET'ten türetilir.
    ENCRYPTION_KEY: str = ""
    SECURITY_HEADERS_ENABLED: bool = True
    HSTS_MAX_AGE: int = 31_536_000
    CSP_POLICY: str = (
        "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; "
        "script-src 'self'; connect-src 'self'; frame-ancestors 'none'; "
        "base-uri 'self'; form-action 'self'"
    )
    # Audit log kayıtları HMAC zinciriyle imzalanır (değişmezlik kanıtı).
    AUDIT_LOG_SIGNING_ENABLED: bool = True

    # Rate limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_BACKEND: Literal["memory", "redis"] = "memory"
    RATE_LIMIT_REQUESTS: int = 300
    RATE_LIMIT_WINDOW_SECONDS: int = 60
    # Kimlik doğrulama uçları için daha sıkı limit (credential stuffing'e karşı).
    RATE_LIMIT_AUTH_REQUESTS: int = 10
    RATE_LIMIT_AUTH_WINDOW_SECONDS: int = 60

    # Log'larda kişisel veri maskeleme
    LOG_PII_MASKING: bool = True

    # ---------- Faz 7: bildirimler ----------
    EMAIL_PROVIDER: Literal["console", "resend", "sendgrid"] = "console"
    EMAIL_FROM: str = "DocAssistant <no-reply@docassistant.local>"
    EMAIL_API_KEY: str = ""
    EMAIL_TIMEOUT_SECONDS: int = 10
    FRONTEND_BASE_URL: str = "http://localhost:5173"

    # ---------- Faz 7: gözlemlenebilirlik ----------
    # DSN boşsa Sentry devre dışı kalır.
    SENTRY_DSN: str = ""
    SENTRY_TRACES_SAMPLE_RATE: float = 0.1
    METRICS_ENABLED: bool = True

    # ---------- Faz 7: i18n & feature flags ----------
    DEFAULT_LOCALE: Literal["tr", "en"] = "tr"
    # Virgülle ayrılmış aktif flag listesi (ör. "onboarding,landing").
    FEATURE_FLAGS: str = "onboarding"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def feature_flag_set(self) -> set[str]:
        return {f.strip() for f in self.FEATURE_FLAGS.split(",") if f.strip()}


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
