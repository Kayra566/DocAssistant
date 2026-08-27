from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, PermissionError
from app.models.collab import DocumentComment
from app.models.enums import ROLE_LEVEL, Role
from app.models.user import User
from app.services import activity
from app.services.documents import get_document
from app.services.organization import get_membership


async def create_comment(
    db: AsyncSession,
    *,
    org_id: uuid.UUID,
    user_id: uuid.UUID,
    document_id: uuid.UUID,
    content: str,
    page: int | None,
) -> DocumentComment:
    doc = await get_document(db, org_id, document_id)
    comment = DocumentComment(
        organization_id=org_id,
        document_id=doc.id,
        user_id=user_id,
        content=content.strip(),
        page=page,
    )
    db.add(comment)
    await db.commit()
    await db.refresh(comment)

    await activity.log(
        db,
        org_id=org_id,
        user_id=user_id,
        action=activity.COMMENT_CREATED,
        resource_type="document",
        resource_id=doc.id,
    )
    return comment


async def list_comments(
    db: AsyncSession, org_id: uuid.UUID, document_id: uuid.UUID
) -> list[tuple[DocumentComment, User | None]]:
    rows = (
        await db.execute(
            select(DocumentComment, User)
            .outerjoin(User, User.id == DocumentComment.user_id)
            .where(
                DocumentComment.organization_id == org_id,
                DocumentComment.document_id == document_id,
            )
            .order_by(DocumentComment.created_at.asc())
        )
    ).all()
    return [(row[0], row[1]) for row in rows]


async def delete_comment(
    db: AsyncSession, org_id: uuid.UUID, comment_id: uuid.UUID, user: User
) -> None:
    """Yorumu yazarı veya organizasyon adminleri silebilir."""
    comment = (
        await db.execute(
            select(DocumentComment).where(
                DocumentComment.id == comment_id,
                DocumentComment.organization_id == org_id,
            )
        )
    ).scalar_one_or_none()
    if not comment:
        raise NotFoundError("Yorum bulunamadı.")

    if comment.user_id != user.id:
        membership = await get_membership(db, user.id, org_id)
        if not membership or ROLE_LEVEL[membership.role] < ROLE_LEVEL[Role.ADMIN]:
            raise PermissionError("Bu yorumu silme yetkiniz yok.")

    document_id = comment.document_id
    await db.delete(comment)
    await db.commit()

    await activity.log(
        db,
        org_id=org_id,
        user_id=user.id,
        action=activity.COMMENT_DELETED,
        resource_type="document",
        resource_id=document_id,
    )
