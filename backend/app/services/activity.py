from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import audit
from app.core.config import settings
from app.core.time import utcnow
from app.models.collab import ActivityLog
from app.models.user import User

# İşlem geçmişinde kullanılan aksiyon adları.
DOCUMENT_UPLOADED = "document.uploaded"
DOCUMENT_DELETED = "document.deleted"
DOCUMENT_DOWNLOADED = "document.downloaded"
SHARE_CREATED = "share.created"
SHARE_REVOKED = "share.revoked"
SHARE_ACCESSED = "share.accessed"
COMMENT_CREATED = "comment.created"
COMMENT_DELETED = "comment.deleted"
EXPORT_CREATED = "export.created"


async def log(
    db: AsyncSession,
    *,
    org_id: uuid.UUID,
    user_id: uuid.UUID | None,
    action: str,
    resource_type: str,
    resource_id: uuid.UUID | None = None,
    meta: dict[str, Any] | None = None,
) -> ActivityLog:
    """Kaydı ekler ve commit eder. Ana işlemi bozmaması için çağıran tarafta izole edilir."""
    # id ve created_at imzalamadan önce sabitlenir; aksi halde flush sırasında
    # atanan değerler imzayla uyuşmaz ve zincir doğrulaması başarısız olur.
    entry = ActivityLog(
        id=uuid.uuid4(),
        created_at=utcnow(),
        organization_id=org_id,
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        meta=meta,
    )
    if settings.AUDIT_LOG_SIGNING_ENABLED:
        previous = await audit.latest_signature(db, org_id)
        entry.prev_signature = previous
        entry.signature = audit.sign(entry, previous)
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry


async def list_activity(
    db: AsyncSession,
    org_id: uuid.UUID,
    *,
    limit: int | None = None,
    offset: int = 0,
    action: str | None = None,
) -> list[tuple[ActivityLog, User | None]]:
    stmt = (
        select(ActivityLog, User)
        .outerjoin(User, User.id == ActivityLog.user_id)
        .where(ActivityLog.organization_id == org_id)
        .order_by(ActivityLog.created_at.desc())
        .limit(limit or settings.ACTIVITY_LOG_PAGE_SIZE)
        .offset(offset)
    )
    if action:
        stmt = stmt.where(ActivityLog.action == action)
    return [(row[0], row[1]) for row in (await db.execute(stmt)).all()]


async def count_activity(db: AsyncSession, org_id: uuid.UUID) -> int:
    return int(
        (
            await db.execute(
                select(func.count())
                .select_from(ActivityLog)
                .where(ActivityLog.organization_id == org_id)
            )
        ).scalar_one()
    )
