"""GDPR: veri taşınabilirliği (Art. 20) ve unutulma hakkı (Art. 17)."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import security
from app.core.exceptions import AuthError
from app.core.logging import get_logger
from app.core.storage import get_storage
from app.models.ai import AIJob, ChatMessage, Conversation
from app.models.billing import Subscription
from app.models.collab import ActivityLog, DocumentComment, ExportJob, ShareLink
from app.models.document import Document
from app.models.enums import Role
from app.models.notification import Notification
from app.models.organization import Membership, Organization
from app.models.user import User

logger = get_logger(__name__)


def _rows(items, fields: tuple[str, ...]) -> list[dict[str, Any]]:
    return [{field: getattr(item, field) for field in fields} for item in items]


async def _scalars(db: AsyncSession, stmt):
    return list((await db.execute(stmt)).scalars().all())


async def _user_org_ids(db: AsyncSession, user_id: uuid.UUID) -> list[uuid.UUID]:
    return list(
        (
            await db.execute(
                select(Membership.organization_id).where(Membership.user_id == user_id)
            )
        )
        .scalars()
        .all()
    )


async def export_user_data(db: AsyncSession, user: User) -> dict[str, Any]:
    """Kullanıcının erişebildiği tüm verinin makine okunur dökümü."""
    org_ids = await _user_org_ids(db, user.id)

    memberships = await _scalars(
        db, select(Membership).where(Membership.user_id == user.id)
    )
    organizations = (
        await _scalars(db, select(Organization).where(Organization.id.in_(org_ids)))
        if org_ids
        else []
    )
    documents = (
        await _scalars(
            db, select(Document).where(Document.organization_id.in_(org_ids))
        )
        if org_ids
        else []
    )
    ai_jobs = await _scalars(db, select(AIJob).where(AIJob.user_id == user.id))
    conversations = await _scalars(
        db, select(Conversation).where(Conversation.user_id == user.id)
    )
    messages = (
        await _scalars(
            db,
            select(ChatMessage).where(
                ChatMessage.conversation_id.in_([c.id for c in conversations])
            ),
        )
        if conversations
        else []
    )
    comments = await _scalars(
        db, select(DocumentComment).where(DocumentComment.user_id == user.id)
    )
    shares = await _scalars(db, select(ShareLink).where(ShareLink.created_by == user.id))
    exports = await _scalars(db, select(ExportJob).where(ExportJob.user_id == user.id))
    activity = await _scalars(
        db, select(ActivityLog).where(ActivityLog.user_id == user.id)
    )
    notifications = await _scalars(
        db, select(Notification).where(Notification.user_id == user.id)
    )
    subscriptions = (
        await _scalars(
            db, select(Subscription).where(Subscription.organization_id.in_(org_ids))
        )
        if org_ids
        else []
    )

    return {
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "is_verified": user.is_verified,
            "totp_enabled": user.totp_enabled,
            "created_at": user.created_at,
        },
        "organizations": _rows(organizations, ("id", "name", "slug", "plan", "created_at")),
        "memberships": _rows(memberships, ("organization_id", "role", "created_at")),
        "documents": _rows(
            documents,
            ("id", "organization_id", "filename", "file_type", "size_bytes",
             "status", "page_count", "created_at"),
        ),
        "ai_jobs": _rows(
            ai_jobs, ("id", "type", "status", "params", "result", "tokens_used", "created_at")
        ),
        "conversations": _rows(conversations, ("id", "document_id", "title", "created_at")),
        "chat_messages": _rows(
            messages, ("id", "conversation_id", "role", "content", "created_at")
        ),
        "comments": _rows(comments, ("id", "document_id", "page", "content", "created_at")),
        "share_links": _rows(
            shares, ("id", "document_id", "permission", "expires_at", "revoked", "created_at")
        ),
        "exports": _rows(exports, ("id", "ai_job_id", "format", "filename", "created_at")),
        "activity": _rows(
            activity, ("id", "action", "resource_type", "resource_id", "created_at")
        ),
        "notifications": _rows(
            notifications, ("id", "type", "title", "body", "read", "created_at")
        ),
        "subscriptions": _rows(
            subscriptions, ("id", "organization_id", "plan", "status", "current_period_end")
        ),
    }


async def _sole_owner_org_ids(db: AsyncSession, user_id: uuid.UUID) -> list[uuid.UUID]:
    """Kullanıcının tek sahibi olduğu organizasyonlar (silinmeleri gerekir)."""
    owned = list(
        (
            await db.execute(
                select(Membership.organization_id).where(
                    Membership.user_id == user_id, Membership.role == Role.OWNER
                )
            )
        )
        .scalars()
        .all()
    )
    if not owned:
        return []

    other_owners = set(
        (
            await db.execute(
                select(Membership.organization_id)
                .where(
                    Membership.organization_id.in_(owned),
                    Membership.role == Role.OWNER,
                    Membership.user_id != user_id,
                )
                .group_by(Membership.organization_id)
                .having(func.count() > 0)
            )
        )
        .scalars()
        .all()
    )
    return [org_id for org_id in owned if org_id not in other_owners]


async def delete_account(db: AsyncSession, user: User, password: str) -> dict[str, int]:
    """Hesabı ve tek sahibi olunan organizasyonları kalıcı olarak siler."""
    if not security.verify_password(password, user.hashed_password):
        raise AuthError("Parola hatalı.")

    doomed_orgs = await _sole_owner_org_ids(db, user.id)

    storage = get_storage()
    removed_files = 0
    if doomed_orgs:
        documents = await _scalars(
            db, select(Document).where(Document.organization_id.in_(doomed_orgs))
        )
        for document in documents:
            try:
                storage.delete(document.storage_key)
                removed_files += 1
            except Exception as exc:  # depolama hatası silmeyi engellememeli
                logger.warning("Depolama nesnesi silinemedi: %s", exc)

        exports = await _scalars(
            db, select(ExportJob).where(ExportJob.organization_id.in_(doomed_orgs))
        )
        for export in exports:
            if export.storage_key:
                try:
                    storage.delete(export.storage_key)
                    removed_files += 1
                except Exception as exc:
                    logger.warning("Export nesnesi silinemedi: %s", exc)

        for org in await _scalars(
            db, select(Organization).where(Organization.id.in_(doomed_orgs))
        ):
            await db.delete(org)

    await db.delete(user)
    await db.commit()
    return {"organizations_deleted": len(doomed_orgs), "files_deleted": removed_files}
