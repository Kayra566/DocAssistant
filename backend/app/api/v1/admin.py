from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_superuser
from app.core.database import get_db
from app.models.user import User
from app.schemas.dashboard import PlatformOrganizationResponse, PlatformStatsResponse
from app.services import dashboard as dashboard_service

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/stats", response_model=PlatformStatsResponse)
async def platform_stats(
    user: User = Depends(require_superuser),
    db: AsyncSession = Depends(get_db),
):
    return PlatformStatsResponse(**await dashboard_service.platform_stats(db))


@router.get("/organizations", response_model=list[PlatformOrganizationResponse])
async def platform_organizations(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(require_superuser),
    db: AsyncSession = Depends(get_db),
):
    rows = await dashboard_service.platform_organizations(db, limit=limit, offset=offset)
    return [PlatformOrganizationResponse(**row) for row in rows]
