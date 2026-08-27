from fastapi import APIRouter

from app.api.v1 import ai, ai_tools, auth, billing, documents, organizations
from app.core.config import settings

router = APIRouter()

router.include_router(auth.router)
router.include_router(organizations.router)
router.include_router(documents.router)
router.include_router(ai.router)
router.include_router(ai_tools.router)
router.include_router(billing.router)


@router.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    """Liveness probe."""
    return {"status": "ok"}


@router.get("/ready", tags=["system"])
async def ready() -> dict[str, str]:
    """Readiness probe. Faz ilerledikçe DB/Redis kontrolleri eklenecek."""
    return {"status": "ready", "environment": settings.ENVIRONMENT}
