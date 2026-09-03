from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1 import (
    admin,
    ai,
    ai_tools,
    auth,
    billing,
    dashboard,
    documents,
    exports,
    gdpr,
    models,
    notifications,
    organizations,
    shares,
)
from app.core.config import settings
from app.core.database import get_db
from app.schemas.system import FeatureFlagsResponse

router = APIRouter()

router.include_router(auth.router)
router.include_router(organizations.router)
router.include_router(documents.router)
router.include_router(ai.router)
router.include_router(ai_tools.router)
router.include_router(billing.router)
router.include_router(dashboard.router)
router.include_router(shares.router)
router.include_router(exports.router)
router.include_router(admin.router)
router.include_router(notifications.router)
router.include_router(gdpr.router)
router.include_router(models.router)


@router.get("/features", response_model=FeatureFlagsResponse, tags=["system"])
async def features() -> FeatureFlagsResponse:
    """İstemcinin davranışını ayarlaması için aktif feature flag'ler."""
    return FeatureFlagsResponse(
        flags=sorted(settings.feature_flag_set),
        environment=settings.ENVIRONMENT,
        default_locale=settings.DEFAULT_LOCALE,
        sentry_enabled=bool(settings.SENTRY_DSN),
    )


@router.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    """Liveness probe — bağımlılıklara dokunmaz."""
    return {"status": "ok"}


@router.get("/ready", tags=["system"])
async def ready(db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    """Readiness probe — Postgres ve Redis erişimini doğrular."""
    checks = {"database": "down", "redis": "down"}

    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = "up"
    except Exception:
        pass

    try:
        import redis.asyncio as aioredis

        client = aioredis.from_url(settings.REDIS_URL)
        await client.ping()
        await client.aclose()
        checks["redis"] = "up"
    except Exception:
        pass

    healthy = all(value == "up" for value in checks.values())
    return {
        "status": "ready" if healthy else "degraded",
        "environment": settings.ENVIRONMENT,
        **checks,
    }
