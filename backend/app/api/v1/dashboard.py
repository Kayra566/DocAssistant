import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_role
from app.core.database import get_db
from app.models.enums import Role
from app.models.user import User
from app.schemas.collab import ActivityResponse
from app.schemas.dashboard import DashboardStatsResponse
from app.services import activity as activity_service
from app.services import dashboard as dashboard_service

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

require_viewer = require_role(Role.VIEWER)


@router.get("/{org_id}/stats", response_model=DashboardStatsResponse)
async def stats(
    org_id: uuid.UUID,
    user: User = Depends(require_viewer),
    db: AsyncSession = Depends(get_db),
):
    return DashboardStatsResponse(**await dashboard_service.org_stats(db, org_id))


@router.get("/{org_id}/activity", response_model=list[ActivityResponse])
async def activity(
    org_id: uuid.UUID,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    action: str | None = Query(default=None),
    user: User = Depends(require_viewer),
    db: AsyncSession = Depends(get_db),
):
    rows = await activity_service.list_activity(
        db, org_id, limit=limit, offset=offset, action=action
    )
    return [
        ActivityResponse(
            id=entry.id,
            action=entry.action,
            resource_type=entry.resource_type,
            resource_id=entry.resource_id,
            meta=entry.meta,
            actor_email=actor.email if actor else None,
            created_at=entry.created_at,
        )
        for entry, actor in rows
    ]
