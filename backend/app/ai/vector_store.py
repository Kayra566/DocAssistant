from __future__ import annotations

import math
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document, DocumentChunk, DocumentStatus


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b, strict=False))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


async def search_chunks(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    query_embedding: list[float],
    document_id: uuid.UUID | None = None,
    top_k: int = 5,
) -> list[tuple[DocumentChunk, float]]:
    """Tenant kapsamında en benzer chunk'ları döndürür (kosinüs, Python içi).

    Not: Üretim ölçeğinde native pgvector `<=>` operatörüyle değiştirilebilir.
    """
    stmt = (
        select(DocumentChunk)
        .join(Document, Document.id == DocumentChunk.document_id)
        .where(
            DocumentChunk.organization_id == tenant_id,
            Document.status == DocumentStatus.READY,
        )
    )
    if document_id is not None:
        stmt = stmt.where(DocumentChunk.document_id == document_id)

    chunks = list((await db.execute(stmt)).scalars().all())
    scored = [
        (c, cosine_similarity(query_embedding, c.embedding or []))
        for c in chunks
    ]
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:top_k]
