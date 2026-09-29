"""Embedding sağlayıcısı değiştiğinde mevcut chunk'ları yeniden vektörleştirir.

Chunk metinleri veritabanında durduğu için dosyaları yeniden işlemeye gerek yoktur.
"""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.embeddings import get_embedder
from app.core.logging import get_logger
from app.models.document import DocumentChunk

logger = get_logger(__name__)

BATCH_SIZE = 64


async def index_status(db: AsyncSession, org_id: uuid.UUID) -> dict[str, int | bool]:
    """Kaç chunk'ın güncel embedding boyutuyla uyuştuğunu raporlar.

    Boyut uyuşmazlığı çökmeye değil, sessizce 0 benzerliğe yol açar; bu yüzden
    arayüzde açıkça gösterilir.
    """
    embedder = get_embedder()
    rows = (
        await db.execute(
            select(DocumentChunk.embedding).where(
                DocumentChunk.organization_id == org_id
            )
        )
    ).scalars()

    total = 0
    stale = 0
    current_dim = embedder.dim
    for embedding in rows:
        total += 1
        length = len(embedding or [])
        if current_dim and length != current_dim:
            stale += 1
        elif not current_dim and length == 0:
            stale += 1

    return {
        "total_chunks": total,
        "stale_chunks": stale,
        "dimension": current_dim,
        "provider": embedder.provider,
        "needs_reindex": stale > 0,
    }


async def reindex_organization(db: AsyncSession, org_id: uuid.UUID) -> dict[str, int]:
    """Organizasyonun tüm chunk'larını mevcut sağlayıcıyla yeniden gömer."""
    embedder = get_embedder()
    total = int(
        (
            await db.execute(
                select(func.count())
                .select_from(DocumentChunk)
                .where(DocumentChunk.organization_id == org_id)
            )
        ).scalar_one()
    )

    updated = 0
    offset = 0
    while offset < total:
        chunks = list(
            (
                await db.execute(
                    select(DocumentChunk)
                    .where(DocumentChunk.organization_id == org_id)
                    .order_by(DocumentChunk.id)
                    .limit(BATCH_SIZE)
                    .offset(offset)
                )
            )
            .scalars()
            .all()
        )
        if not chunks:
            break

        vectors = await embedder.embed_many([c.content for c in chunks])
        for chunk, vector in zip(chunks, vectors, strict=True):
            chunk.embedding = vector
        await db.commit()

        updated += len(chunks)
        offset += BATCH_SIZE

    logger.info("Reindex tamamlandi: %s/%s chunk", updated, total)
    return {"reindexed": updated, "total": total}
