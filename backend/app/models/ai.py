import enum
import uuid

from sqlalchemy import (
    JSON,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class AIJobType(enum.StrEnum):
    CHAT = "chat"
    SUMMARY = "summary"
    KEYPOINTS = "keypoints"
    QUIZ = "quiz"
    TRANSLATE = "translate"
    EXTRACT = "extract"
    COMPARE = "compare"


class AIJobStatus(enum.StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


class AIJob(BaseModel):
    __tablename__ = "ai_jobs"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    document_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("documents.id", ondelete="SET NULL"), nullable=True
    )
    type: Mapped[AIJobType] = mapped_column(Enum(AIJobType, native_enum=False))
    status: Mapped[AIJobStatus] = mapped_column(
        Enum(AIJobStatus, native_enum=False), default=AIJobStatus.PENDING
    )
    tokens_used: Mapped[int] = mapped_column(Integer, default=0)
    cost: Mapped[float] = mapped_column(Numeric(10, 6), default=0)


class Conversation(BaseModel):
    __tablename__ = "conversations"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("documents.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(255), default="Yeni sohbet")

    messages: Mapped[list["ChatMessage"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="ChatMessage.created_at",
    )


class ChatMessage(BaseModel):
    __tablename__ = "chat_messages"

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("conversations.id", ondelete="CASCADE"), index=True
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    role: Mapped[str] = mapped_column(String(16))  # user | assistant
    content: Mapped[str] = mapped_column(Text)
    # Kaynak referansları: [{document_id, page, chunk_index, snippet, score}]
    citations: Mapped[list | None] = mapped_column(JSON, nullable=True)
    tokens: Mapped[int] = mapped_column(Integer, default=0)

    conversation: Mapped["Conversation"] = relationship(back_populates="messages")
