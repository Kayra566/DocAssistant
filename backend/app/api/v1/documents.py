import uuid

from fastapi import APIRouter, Depends, UploadFile
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_role
from app.core import security
from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import AppError, AuthError, NotFoundError
from app.core.storage import get_storage
from app.models.enums import Role
from app.models.user import User
from app.schemas.document import (
    BatchUploadResult,
    DocumentDownloadResponse,
    DocumentResponse,
    FavoriteRequest,
)
from app.services import documents as doc_service

router = APIRouter(prefix="/documents", tags=["documents"])

# Rol bağımlılıklarını modül seviyesinde kur (B008: default içinde çağrı yapma).
require_viewer = require_role(Role.VIEWER)
require_member = require_role(Role.MEMBER)


@router.get("/download")
async def download_file(token: str, db: AsyncSession = Depends(get_db)):
    """İmzalı token ile dosya indirir (signed URL hedefi)."""
    try:
        doc_id = security.verify_download_token(token)
    except Exception as exc:
        raise AuthError("İndirme bağlantısı geçersiz veya süresi dolmuş.") from exc

    from app.models.document import Document

    doc = await db.get(Document, uuid.UUID(doc_id))
    if not doc:
        raise NotFoundError("Doküman bulunamadı.")
    data = get_storage().get(doc.storage_key)
    return Response(
        content=data,
        media_type=doc.mime_type,
        headers={"Content-Disposition": f'attachment; filename="{doc.filename}"'},
    )


@router.get("/{org_id}", response_model=list[DocumentResponse])
async def list_documents(
    org_id: uuid.UUID,
    user: User = Depends(require_viewer),
    db: AsyncSession = Depends(get_db),
):
    docs = await doc_service.list_documents(db, org_id)
    return [DocumentResponse.model_validate(d) for d in docs]


@router.post("/{org_id}/upload", response_model=DocumentResponse, status_code=201)
async def upload_document(
    org_id: uuid.UUID,
    file: UploadFile,
    user: User = Depends(require_member),
    db: AsyncSession = Depends(get_db),
):
    data = await file.read()
    doc = await doc_service.upload_document(
        db,
        org_id=org_id,
        owner_id=user.id,
        filename=file.filename or "untitled",
        data=data,
    )
    return DocumentResponse.model_validate(doc)


@router.post("/{org_id}/batch-upload", response_model=BatchUploadResult)
async def batch_upload(
    org_id: uuid.UUID,
    files: list[UploadFile],
    user: User = Depends(require_member),
    db: AsyncSession = Depends(get_db),
):
    uploaded = []
    errors = []
    for f in files:
        try:
            data = await f.read()
            doc = await doc_service.upload_document(
                db,
                org_id=org_id,
                owner_id=user.id,
                filename=f.filename or "untitled",
                data=data,
            )
            uploaded.append(DocumentResponse.model_validate(doc))
        except AppError as exc:
            errors.append({"filename": f.filename or "untitled", "error": exc.message})
    return BatchUploadResult(uploaded=uploaded, errors=errors)


@router.get("/{org_id}/{doc_id}", response_model=DocumentResponse)
async def get_document(
    org_id: uuid.UUID,
    doc_id: uuid.UUID,
    user: User = Depends(require_viewer),
    db: AsyncSession = Depends(get_db),
):
    doc = await doc_service.get_document(db, org_id, doc_id)
    return DocumentResponse.model_validate(doc)


@router.get("/{org_id}/{doc_id}/download-url", response_model=DocumentDownloadResponse)
async def get_download_url(
    org_id: uuid.UUID,
    doc_id: uuid.UUID,
    user: User = Depends(require_viewer),
    db: AsyncSession = Depends(get_db),
):
    doc = await doc_service.get_document(db, org_id, doc_id)
    token = security.create_download_token(str(doc.id))
    return DocumentDownloadResponse(
        url=f"{settings.API_V1_PREFIX}/documents/download?token={token}",
        expires_in_minutes=settings.SIGNED_URL_EXPIRE_MINUTES,
    )


@router.post("/{org_id}/{doc_id}/favorite", response_model=DocumentResponse)
async def set_favorite(
    org_id: uuid.UUID,
    doc_id: uuid.UUID,
    payload: FavoriteRequest,
    user: User = Depends(require_member),
    db: AsyncSession = Depends(get_db),
):
    doc = await doc_service.set_favorite(db, org_id, doc_id, payload.is_favorite)
    return DocumentResponse.model_validate(doc)


@router.delete("/{org_id}/{doc_id}", status_code=204)
async def delete_document(
    org_id: uuid.UUID,
    doc_id: uuid.UUID,
    user: User = Depends(require_member),
    db: AsyncSession = Depends(get_db),
):
    await doc_service.delete_document(db, org_id, doc_id)
    return Response(status_code=204)
