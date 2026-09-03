from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

from app.api.v1.router import router as api_v1_router
from app.core.config import settings
from app.core.exceptions import AppError
from app.core.i18n import normalize_locale, translate
from app.core.logging import configure_logging, get_logger
from app.core.middleware import (
    MetricsMiddleware,
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
)
from app.core.observability import init_sentry

DESCRIPTION = """
DocAssistant — dokümanlarınızla sohbet edin, özetleyin, çevirin ve dışa aktarın.

**Kimlik doğrulama:** `POST /api/v1/auth/login` ile alınan `access_token`'ı
`Authorization: Bearer <token>` başlığında gönderin.

**Çok kiracılılık:** Kaynak uçları `org_id` içerir ve rol bazlı yetkilendirmeye tabidir
(Owner > Admin > Member > Viewer).
"""

TAGS_METADATA = [
    {"name": "auth", "description": "Kayıt, giriş, token yenileme, 2FA."},
    {"name": "organizations", "description": "Organizasyon, üyelik ve davetler."},
    {"name": "documents", "description": "Doküman yükleme, işleme, indirme ve notlar."},
    {"name": "ai", "description": "Doküman sohbeti (RAG) ve kaynak referansları."},
    {"name": "ai-tools", "description": "Özet, kritik bilgi, quiz, çeviri, karşılaştırma."},
    {"name": "billing", "description": "Abonelik, kota ve ödeme sağlayıcısı webhook'ları."},
    {"name": "dashboard", "description": "Kullanım istatistikleri ve işlem geçmişi."},
    {"name": "sharing", "description": "Paylaşım bağlantıları ve public erişim."},
    {"name": "exports", "description": "AI sonuçlarının PDF/DOCX/XLSX/MD çıktıları."},
    {"name": "notifications", "description": "Uygulama içi bildirimler."},
    {"name": "gdpr", "description": "Veri dışa aktarma ve hesap silme."},
    {"name": "admin", "description": "Platform yönetimi (superuser)."},
    {"name": "system", "description": "Sağlık kontrolleri, metrikler, feature flag'ler."},
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    init_sentry()
    logger = get_logger(__name__)
    logger.info("Starting %s (%s)", settings.APP_NAME, settings.ENVIRONMENT)
    yield
    logger.info("Shutting down %s", settings.APP_NAME)


app = FastAPI(
    title=settings.APP_NAME,
    description=DESCRIPTION,
    version="1.0.0",
    docs_url="/docs",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    openapi_tags=TAGS_METADATA,
    lifespan=lifespan,
)


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    # Özel mesaj verilmediyse istemcinin diline göre çeviri döndürülür.
    message = (
        exc.message
        if exc.custom_message
        else translate(exc.code, normalize_locale(request.headers.get("accept-language")))
    )
    return JSONResponse(status_code=exc.status_code, content={"detail": message})


# Middleware sırası ters uygulanır: güvenlik başlıkları en dışta kalır.
app.add_middleware(MetricsMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)


@app.get("/", tags=["system"])
async def root() -> dict[str, str]:
    return {"app": settings.APP_NAME, "docs": "/docs"}


@app.get("/health", tags=["system"], include_in_schema=False)
async def liveness() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/metrics", tags=["system"], include_in_schema=False)
async def metrics() -> Response:
    if not settings.METRICS_ENABLED:
        return Response(status_code=404)
    from app.core.metrics import render

    payload, content_type = render()
    return Response(content=payload, media_type=content_type)
