import uuid

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_role
from app.core.database import get_db
from app.core.exceptions import PermissionError
from app.core.storage import get_storage
from app.models.collab import SharePermission
from app.models.enums import Role
from app.models.organization import Organization
from app.models.user import User
from app.schemas.collab import (
    SharedDocumentResponse,
    ShareLinkCreate,
    ShareLinkCreated,
    ShareLinkResponse,
)
from app.services import sharing

router = APIRouter(prefix="/shares", tags=["sharing"])

require_viewer = require_role(Role.VIEWER)
require_member = require_role(Role.MEMBER)


@router.get("/public/{token}", response_model=SharedDocumentResponse)
async def public_share(
    token: str,
    email: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    """Paylaşım bağlantısının hedeflediği dokümanın herkese açık özeti."""
    link, doc = await sharing.resolve_share(db, token, email)
    await sharing.register_access(db, link)
    org = await db.get(Organization, link.organization_id)
    return SharedDocumentResponse(
        filename=doc.filename,
        file_type=doc.file_type,
        size_bytes=doc.size_bytes,
        page_count=doc.page_count,
        permission=link.permission,
        can_download=sharing.can_download(link),
        expires_at=link.expires_at,
        organization_name=org.name if org else "",
    )


@router.get("/public/{token}/download")
async def public_share_download(
    token: str,
    email: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    link, doc = await sharing.resolve_share(db, token, email)
    if not sharing.can_download(link):
        raise PermissionError("Bu bağlantı yalnızca görüntüleme izni veriyor.")
    await sharing.register_access(db, link)
    return Response(
        content=get_storage().get(doc.storage_key),
        media_type=doc.mime_type,
        headers={"Content-Disposition": f'attachment; filename="{doc.id}.{doc.file_type}"'},
    )


@router.post("/{org_id}", response_model=ShareLinkCreated, status_code=201)
async def create_share(
    org_id: uuid.UUID,
    payload: ShareLinkCreate,
    user: User = Depends(require_member),
    db: AsyncSession = Depends(get_db),
):
    link, raw_token = await sharing.create_share_link(
        db,
        org_id=org_id,
        user_id=user.id,
        document_id=payload.document_id,
        permission=SharePermission(payload.permission),
        email=str(payload.email) if payload.email else None,
        expires_in_hours=payload.expires_in_hours,
    )
    return ShareLinkCreated(
        **ShareLinkResponse.model_validate(link).model_dump(),
        token=raw_token,
        url=sharing.share_url(raw_token),
    )


@router.get("/{org_id}", response_model=list[ShareLinkResponse])
async def list_shares(
    org_id: uuid.UUID,
    document_id: uuid.UUID | None = Query(default=None),
    user: User = Depends(require_viewer),
    db: AsyncSession = Depends(get_db),
):
    links = await sharing.list_share_links(db, org_id, document_id)
    return [ShareLinkResponse.model_validate(link) for link in links]


@router.delete("/{org_id}/{share_id}", response_model=ShareLinkResponse)
async def revoke_share(
    org_id: uuid.UUID,
    share_id: uuid.UUID,
    user: User = Depends(require_member),
    db: AsyncSession = Depends(get_db),
):
    link = await sharing.revoke_share_link(db, org_id, share_id, user.id)
    return ShareLinkResponse.model_validate(link)
