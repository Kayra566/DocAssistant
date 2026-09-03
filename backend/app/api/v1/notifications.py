import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.system import NotificationResponse, UnreadCountResponse
from app.services import notifications as service

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationResponse])
async def list_notifications(
    unread_only: bool = Query(default=False),
    limit: int = Query(default=50, ge=1, le=200),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rows = await service.list_for_user(
        db, user.id, unread_only=unread_only, limit=limit
    )
    return [NotificationResponse.model_validate(row) for row in rows]


@router.get("/unread-count", response_model=UnreadCountResponse)
async def unread_count(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return UnreadCountResponse(unread=await service.unread_count(db, user.id))


@router.post("/{notification_id}/read", response_model=NotificationResponse)
async def mark_read(
    notification_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return NotificationResponse.model_validate(
        await service.mark_read(db, user.id, notification_id)
    )


@router.post("/read-all", response_model=UnreadCountResponse)
async def mark_all_read(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await service.mark_all_read(db, user.id)
    return UnreadCountResponse(unread=0)
