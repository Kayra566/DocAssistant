from fastapi import APIRouter

from app.core.config import settings

router = APIRouter()


@router.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    """Liveness probe."""
    return {"status": "ok"}


@router.get("/ready", tags=["system"])
async def ready() -> dict[str, str]:
    """Readiness probe. Faz ilerledikçe DB/Redis kontrolleri eklenecek."""
    return {"status": "ready", "environment": settings.ENVIRONMENT}
