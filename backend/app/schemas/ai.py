import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class Citation(BaseModel):
    document_id: str
    page: int
    chunk_index: int
    snippet: str
    score: float


class ChatRequest(BaseModel):
    document_id: uuid.UUID
    question: str
    conversation_id: uuid.UUID | None = None


class ChatResponse(BaseModel):
    conversation_id: uuid.UUID
    message_id: uuid.UUID
    answer: str
    citations: list[Citation]
    tokens_used: int
    cache_hit: bool


class ConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    document_id: uuid.UUID
    title: str
    created_at: datetime


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    role: str
    content: str
    citations: list[Citation] | None
    tokens: int
    created_at: datetime


class UsageResponse(BaseModel):
    plan: str
    ai_tokens_used: int
    ai_tokens_limit: int
