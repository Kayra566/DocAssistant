from __future__ import annotations

import uuid

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.notification import Notification, NotificationType


async def create(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    title: str,
    body: str,
    type: NotificationType = NotificationType.SYSTEM,
    org_id: uuid.UUID | None = None,
    link: str | None = None,
) -> Notification:
    notification = Notification(
        user_id=user_id,
        organization_id=org_id,
        type=type,
        title=title,
        body=body,
        link=link,
    )
    db.add(notification)
    await db.commit()
    await db.refresh(notification)
    return notification


async def list_for_user(
    db: AsyncSession, user_id: uuid.UUID, *, unread_only: bool = False, limit: int = 50
) -> list[Notification]:
    stmt = (
        select(Notification)
        .where(Notification.user_id == user_id)
        .order_by(Notification.created_at.desc())
        .limit(limit)
    )
    if unread_only:
        stmt = stmt.where(Notification.read.is_(False))
    return list((await db.execute(stmt)).scalars().all())


async def unread_count(db: AsyncSession, user_id: uuid.UUID) -> int:
    return int(
        (
            await db.execute(
                select(func.count())
                .select_from(Notification)
                .where(Notification.user_id == user_id, Notification.read.is_(False))
            )
        ).scalar_one()
    )


async def mark_read(
    db: AsyncSession, user_id: uuid.UUID, notification_id: uuid.UUID
) -> Notification:
    notification = (
        await db.execute(
            select(Notification).where(
                Notification.id == notification_id, Notification.user_id == user_id
            )
        )
    ).scalar_one_or_none()
    if not notification:
        raise NotFoundError("Bildirim bulunamadı.")
    notification.read = True
    await db.commit()
    await db.refresh(notification)
    return notification


async def mark_all_read(db: AsyncSession, user_id: uuid.UUID) -> int:
    result = await db.execute(
        update(Notification)
        .where(Notification.user_id == user_id, Notification.read.is_(False))
        .values(read=True)
    )
    await db.commit()
    return int(result.rowcount or 0)
