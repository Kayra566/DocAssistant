from __future__ import annotations

import uuid
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import security
from app.core.config import settings
from app.core.exceptions import AuthError, NotFoundError, ValidationError
from app.core.time import ensure_utc, utcnow
from app.models.collab import ShareLink, SharePermission
from app.models.document import Document
from app.services import activity
from app.services.documents import get_document


def share_url(raw_token: str) -> str:
    return f"{settings.SHARE_PUBLIC_BASE_URL.rstrip('/')}/{raw_token}"


async def create_share_link(
    db: AsyncSession,
    *,
    org_id: uuid.UUID,
    user_id: uuid.UUID,
    document_id: uuid.UUID,
    permission: SharePermission,
    email: str | None,
    expires_in_hours: int | None,
) -> tuple[ShareLink, str]:
    """Paylaşım bağlantısı oluşturur; ham token yalnızca burada döner."""
    doc = await get_document(db, org_id, document_id)

    hours = expires_in_hours or settings.SHARE_LINK_DEFAULT_EXPIRE_HOURS
    if not 1 <= hours <= settings.SHARE_LINK_MAX_EXPIRE_HOURS:
        raise ValidationError(
            f"Geçerlilik süresi 1-{settings.SHARE_LINK_MAX_EXPIRE_HOURS} saat arasında olmalı."
        )

    raw_token = security.generate_raw_token()
    link = ShareLink(
        organization_id=org_id,
        document_id=doc.id,
        created_by=user_id,
        token_hash=security.hash_token(raw_token),
        permission=permission,
        email=email.strip().lower() if email else None,
        expires_at=utcnow() + timedelta(hours=hours),
    )
    db.add(link)
    await db.commit()
    await db.refresh(link)

    await activity.log(
        db,
        org_id=org_id,
        user_id=user_id,
        action=activity.SHARE_CREATED,
        resource_type="document",
        resource_id=doc.id,
        meta={"filename": doc.filename, "permission": str(permission)},
    )
    return link, raw_token


async def list_share_links(
    db: AsyncSession, org_id: uuid.UUID, document_id: uuid.UUID | None = None
) -> list[ShareLink]:
    stmt = (
        select(ShareLink)
        .where(ShareLink.organization_id == org_id)
        .order_by(ShareLink.created_at.desc())
    )
    if document_id:
        stmt = stmt.where(ShareLink.document_id == document_id)
    return list((await db.execute(stmt)).scalars().all())


async def revoke_share_link(
    db: AsyncSession, org_id: uuid.UUID, share_id: uuid.UUID, user_id: uuid.UUID
) -> ShareLink:
    link = (
        await db.execute(
            select(ShareLink).where(
                ShareLink.id == share_id, ShareLink.organization_id == org_id
            )
        )
    ).scalar_one_or_none()
    if not link:
        raise NotFoundError("Paylaşım bağlantısı bulunamadı.")

    link.revoked = True
    await db.commit()
    await db.refresh(link)

    await activity.log(
        db,
        org_id=org_id,
        user_id=user_id,
        action=activity.SHARE_REVOKED,
        resource_type="share_link",
        resource_id=link.id,
    )
    return link


async def resolve_share(
    db: AsyncSession, raw_token: str, email: str | None = None
) -> tuple[ShareLink, Document]:
    """Public token'ı doğrular. Geçersiz/süresi dolmuş/iptal edilmiş ise 401 üretir."""
    link = (
        await db.execute(
            select(ShareLink).where(
                ShareLink.token_hash == security.hash_token(raw_token)
            )
        )
    ).scalar_one_or_none()
    # Geçersiz token ile iptal/süre bilgisini ayırt etmemek için tek mesaj kullanılır.
    if not link or link.revoked:
        raise AuthError("Paylaşım bağlantısı geçersiz veya süresi dolmuş.")

    expires_at = ensure_utc(link.expires_at)
    if expires_at and expires_at < utcnow():
        raise AuthError("Paylaşım bağlantısı geçersiz veya süresi dolmuş.")

    if link.email and (email or "").strip().lower() != link.email:
        raise AuthError("Bu bağlantı yalnızca davet edilen e-posta ile açılabilir.")

    doc = await db.get(Document, link.document_id)
    if not doc:
        raise NotFoundError("Doküman bulunamadı.")
    return link, doc


async def register_access(db: AsyncSession, link: ShareLink) -> None:
    link.view_count += 1
    link.last_accessed_at = utcnow()
    await db.commit()
    await activity.log(
        db,
        org_id=link.organization_id,
        user_id=None,
        action=activity.SHARE_ACCESSED,
        resource_type="share_link",
        resource_id=link.id,
    )


def can_download(link: ShareLink) -> bool:
    return link.permission == SharePermission.DOWNLOAD
