from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.embeddings import get_embedder
from app.ai.provider import SYSTEM_PROMPT, get_active_provider
from app.ai.vector_store import search_chunks
from app.core.config import settings
from app.models.document import DocumentChunk


async def retrieve(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    document_id: uuid.UUID,
    question: str,
    top_k: int | None = None,
) -> list[tuple[DocumentChunk, float]]:
    embedding = get_embedder().embed(question)
    return await search_chunks(
        db,
        tenant_id=tenant_id,
        query_embedding=embedding,
        document_id=document_id,
        top_k=top_k or settings.RAG_TOP_K,
    )


def build_prompt(chunks: list[DocumentChunk], question: str) -> str:
    context_blocks = [
        f"[Sayfa {c.page}] {c.content}" for c in chunks
    ]
    context = "\n---\n".join(context_blocks) if context_blocks else "(bağlam yok)"
    return f"BAĞLAM:\n{context}\n\nSORU: {question}\n\nYANIT:"


def to_citations(scored: list[tuple[DocumentChunk, float]]) -> list[dict]:
    return [
        {
            "document_id": str(c.document_id),
            "page": c.page,
            "chunk_index": c.chunk_index,
            "snippet": c.content[:200],
            "score": round(float(score), 4),
        }
        for c, score in scored
    ]


async def generate_answer(db: AsyncSession, prompt: str) -> str:
    provider = await get_active_provider(db)
    return await provider.complete(system=SYSTEM_PROMPT, prompt=prompt)
