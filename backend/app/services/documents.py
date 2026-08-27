from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.embeddings import get_embedder
from app.core.config import settings
from app.core.exceptions import NotFoundError
from app.core.storage import get_storage
from app.models.document import Document, DocumentChunk, DocumentStatus
from app.services.quota import ensure_document_quota
from app.utils.chunking import chunk_pages
from app.utils.file_validator import MIME_MAP, detect_file_type, validate_size
from app.utils.text_extractor import extract_pages


async def process_document(db: AsyncSession, document: Document) -> None:
    """Metin çıkar → chunk → embed → kaydet. Hata durumunda FAILED işaretler."""
    document.status = DocumentStatus.PROCESSING
    await db.commit()
    try:
        data = get_storage().get(document.storage_key)
        pages = extract_pages(document.file_type, data)
        chunks = chunk_pages(pages)

        embedder = get_embedder()
        embeddings = embedder.embed_many([c[2] for c in chunks])

        for (idx, page, content), emb in zip(chunks, embeddings, strict=False):
            db.add(
                DocumentChunk(
                    document_id=document.id,
                    organization_id=document.organization_id,
                    chunk_index=idx,
                    page=page,
                    content=content,
                    embedding=emb,
                )
            )
        document.page_count = len(pages)
        document.chunk_count = len(chunks)
        document.status = DocumentStatus.READY
        document.error = None
        await db.commit()
    except Exception as exc:  # işleme hatasını yakala, dokümanı FAILED yap
        await db.rollback()
        document.status = DocumentStatus.FAILED
        document.error = str(exc)[:2000]
        await db.commit()


async def upload_document(
    db: AsyncSession,
    *,
    org_id: uuid.UUID,
    owner_id: uuid.UUID,
    filename: str,
    data: bytes,
) -> Document:
    validate_size(len(data))
    file_type = detect_file_type(filename, data)
    await ensure_document_quota(db, org_id, len(data))

    doc_id = uuid.uuid4()
    storage_key = f"{org_id}/{doc_id}/{filename}"
    get_storage().put(storage_key, data, MIME_MAP.get(file_type, "application/octet-stream"))

    document = Document(
        id=doc_id,
        organization_id=org_id,
        owner_id=owner_id,
        filename=filename,
        storage_key=storage_key,
        mime_type=MIME_MAP.get(file_type, "application/octet-stream"),
        file_type=file_type,
        size_bytes=len(data),
        status=DocumentStatus.UPLOADED,
    )
    db.add(document)
    await db.commit()
    await db.refresh(document)

    if settings.PROCESS_DOCUMENTS_EAGER:
        await process_document(db, document)
        await db.refresh(document)
    else:
        from app.workers.document_tasks import process_document_task

        process_document_task.delay(str(document.id))

    return document


async def list_documents(db: AsyncSession, org_id: uuid.UUID) -> list[Document]:
    rows = (
        await db.execute(
            select(Document)
            .where(Document.organization_id == org_id)
            .order_by(Document.created_at.desc())
        )
    ).scalars().all()
    return list(rows)


async def get_document(
    db: AsyncSession, org_id: uuid.UUID, doc_id: uuid.UUID
) -> Document:
    doc = (
        await db.execute(
            select(Document).where(
                Document.id == doc_id, Document.organization_id == org_id
            )
        )
    ).scalar_one_or_none()
    if not doc:
        raise NotFoundError("Doküman bulunamadı.")
    return doc


async def delete_document(
    db: AsyncSession, org_id: uuid.UUID, doc_id: uuid.UUID
) -> None:
    doc = await get_document(db, org_id, doc_id)
    get_storage().delete(doc.storage_key)
    await db.delete(doc)
    await db.commit()


async def set_favorite(
    db: AsyncSession, org_id: uuid.UUID, doc_id: uuid.UUID, value: bool
) -> Document:
    doc = await get_document(db, org_id, doc_id)
    doc.is_favorite = value
    await db.commit()
    await db.refresh(doc)
    return doc
