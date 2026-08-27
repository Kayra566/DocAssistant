import uuid

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_role
from app.core.database import get_db
from app.models.enums import Role
from app.models.organization import Organization
from app.models.user import User
from app.schemas.ai import (
    ChatRequest,
    ChatResponse,
    ConversationResponse,
    MessageResponse,
    UsageResponse,
)
from app.services import ai_chat
from app.services.quota import ai_token_limit, month_token_usage

router = APIRouter(prefix="/ai", tags=["ai"])

require_viewer = require_role(Role.VIEWER)
require_member = require_role(Role.MEMBER)


@router.post("/{org_id}/chat", response_model=ChatResponse)
async def chat(
    org_id: uuid.UUID,
    payload: ChatRequest,
    user: User = Depends(require_member),
    db: AsyncSession = Depends(get_db),
):
    result = await ai_chat.chat(
        db,
        org_id=org_id,
        user_id=user.id,
        document_id=payload.document_id,
        question=payload.question,
        conversation_id=payload.conversation_id,
    )
    return ChatResponse(**result)


@router.post("/{org_id}/chat/stream")
async def chat_stream(
    org_id: uuid.UUID,
    payload: ChatRequest,
    user: User = Depends(require_member),
    db: AsyncSession = Depends(get_db),
):
    async def event_gen():
        async for token in ai_chat.stream_chat(
            db,
            org_id=org_id,
            document_id=payload.document_id,
            question=payload.question,
        ):
            yield f"data: {token}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_gen(), media_type="text/event-stream")


@router.get(
    "/{org_id}/documents/{document_id}/conversations",
    response_model=list[ConversationResponse],
)
async def list_conversations(
    org_id: uuid.UUID,
    document_id: uuid.UUID,
    user: User = Depends(require_viewer),
    db: AsyncSession = Depends(get_db),
):
    convs = await ai_chat.list_conversations(db, org_id, document_id)
    return [ConversationResponse.model_validate(c) for c in convs]


@router.get(
    "/{org_id}/conversations/{conversation_id}/messages",
    response_model=list[MessageResponse],
)
async def get_messages(
    org_id: uuid.UUID,
    conversation_id: uuid.UUID,
    user: User = Depends(require_viewer),
    db: AsyncSession = Depends(get_db),
):
    msgs = await ai_chat.get_messages(db, org_id, conversation_id)
    return [MessageResponse.model_validate(m) for m in msgs]


@router.get("/{org_id}/usage", response_model=UsageResponse)
async def usage(
    org_id: uuid.UUID,
    user: User = Depends(require_viewer),
    db: AsyncSession = Depends(get_db),
):
    org = await db.get(Organization, org_id)
    used = await month_token_usage(db, org_id)
    return UsageResponse(
        plan=org.plan,
        ai_tokens_used=used,
        ai_tokens_limit=ai_token_limit(org.plan),
    )
