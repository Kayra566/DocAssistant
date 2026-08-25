from __future__ import annotations

import uuid
from collections.abc import AsyncIterator

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai import rag
from app.ai.cache import cache_key, get_cache
from app.ai.guards import moderate_output, sanitize_question
from app.ai.provider import SYSTEM_PROMPT, get_provider
from app.ai.tokens import estimate_tokens
from app.core.config import settings
from app.core.exceptions import NotFoundError
from app.models.ai import AIJob, AIJobStatus, AIJobType, ChatMessage, Conversation
from app.models.document import Document, DocumentStatus
from app.services.quota import ensure_ai_quota


async def _load_ready_document(
    db: AsyncSession, org_id: uuid.UUID, document_id: uuid.UUID
) -> Document:
    doc = (
        await db.execute(
            select(Document).where(
                Document.id == document_id,
                Document.organization_id == org_id,
            )
        )
    ).scalar_one_or_none()
    if not doc:
        raise NotFoundError("Doküman bulunamadı.")
    if doc.status != DocumentStatus.READY:
        raise NotFoundError("Doküman henüz işlenmedi.")
    return doc


async def _get_or_create_conversation(
    db: AsyncSession,
    *,
    org_id: uuid.UUID,
    document_id: uuid.UUID,
    user_id: uuid.UUID,
    conversation_id: uuid.UUID | None,
    first_question: str,
) -> Conversation:
    if conversation_id:
        conv = (
            await db.execute(
                select(Conversation).where(
                    Conversation.id == conversation_id,
                    Conversation.organization_id == org_id,
                )
            )
        ).scalar_one_or_none()
        if not conv:
            raise NotFoundError("Sohbet bulunamadı.")
        return conv

    conv = Conversation(
        organization_id=org_id,
        document_id=document_id,
        user_id=user_id,
        title=first_question[:60],
    )
    db.add(conv)
    await db.flush()
    return conv


async def chat(
    db: AsyncSession,
    *,
    org_id: uuid.UUID,
    user_id: uuid.UUID,
    document_id: uuid.UUID,
    question: str,
    conversation_id: uuid.UUID | None = None,
) -> dict:
    question = sanitize_question(question)
    doc = await _load_ready_document(db, org_id, document_id)

    prompt_estimate = estimate_tokens(question)
    await ensure_ai_quota(db, org_id, prompt_estimate)

    conv = await _get_or_create_conversation(
        db,
        org_id=org_id,
        document_id=document_id,
        user_id=user_id,
        conversation_id=conversation_id,
        first_question=question,
    )

    scored = await rag.retrieve(
        db, tenant_id=org_id, document_id=doc.id, question=question
    )
    prompt = rag.build_prompt([c for c, _ in scored], question)
    citations = rag.to_citations(scored)

    cache = get_cache()
    key = cache_key("chat", str(doc.id), question)
    cached = cache.get(key)
    if cached is not None:
        answer = cached["answer"]
        citations = cached["citations"]
        cache_hit = True
    else:
        answer = moderate_output(await rag.generate_answer(prompt))
        cache.set(
            key, {"answer": answer, "citations": citations}, settings.AI_CACHE_TTL_SECONDS
        )
        cache_hit = False

    tokens = estimate_tokens(prompt) + estimate_tokens(answer)

    db.add(
        ChatMessage(
            conversation_id=conv.id,
            organization_id=org_id,
            role="user",
            content=question,
        )
    )
    assistant_msg = ChatMessage(
        conversation_id=conv.id,
        organization_id=org_id,
        role="assistant",
        content=answer,
        citations=citations,
        tokens=tokens,
    )
    db.add(assistant_msg)

    # Kota takibi için AIJob kaydı (cache hit'te token 0 sayılır).
    db.add(
        AIJob(
            organization_id=org_id,
            user_id=user_id,
            document_id=doc.id,
            type=AIJobType.CHAT,
            status=AIJobStatus.DONE,
            tokens_used=0 if cache_hit else tokens,
        )
    )
    await db.commit()
    await db.refresh(assistant_msg)

    return {
        "conversation_id": conv.id,
        "message_id": assistant_msg.id,
        "answer": answer,
        "citations": citations,
        "tokens_used": 0 if cache_hit else tokens,
        "cache_hit": cache_hit,
    }


async def stream_chat(
    db: AsyncSession,
    *,
    org_id: uuid.UUID,
    document_id: uuid.UUID,
    question: str,
) -> AsyncIterator[str]:
    """SSE için token akışı (kalıcılık yapmaz; hafif önizleme)."""
    question = sanitize_question(question)
    doc = await _load_ready_document(db, org_id, document_id)
    await ensure_ai_quota(db, org_id, estimate_tokens(question))

    scored = await rag.retrieve(
        db, tenant_id=org_id, document_id=doc.id, question=question
    )
    prompt = rag.build_prompt([c for c, _ in scored], question)
    async for token in get_provider().stream(system=SYSTEM_PROMPT, prompt=prompt):
        yield token


async def list_conversations(
    db: AsyncSession, org_id: uuid.UUID, document_id: uuid.UUID
) -> list[Conversation]:
    rows = (
        await db.execute(
            select(Conversation)
            .where(
                Conversation.organization_id == org_id,
                Conversation.document_id == document_id,
            )
            .order_by(Conversation.created_at.desc())
        )
    ).scalars().all()
    return list(rows)


async def get_messages(
    db: AsyncSession, org_id: uuid.UUID, conversation_id: uuid.UUID
) -> list[ChatMessage]:
    conv = (
        await db.execute(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.organization_id == org_id,
            )
        )
    ).scalar_one_or_none()
    if not conv:
        raise NotFoundError("Sohbet bulunamadı.")
    rows = (
        await db.execute(
            select(ChatMessage)
            .where(ChatMessage.conversation_id == conversation_id)
            .order_by(ChatMessage.created_at)
        )
    ).scalars().all()
    return list(rows)
