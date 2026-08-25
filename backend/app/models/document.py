import enum
import uuid

from sqlalchemy import (
    JSON,
    Boolean,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class DocumentStatus(enum.StrEnum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


class Document(BaseModel):
    __tablename__ = "documents"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    filename: Mapped[str] = mapped_column(String(512))
    storage_key: Mapped[str] = mapped_column(String(512))
    mime_type: Mapped[str] = mapped_column(String(128))
    file_type: Mapped[str] = mapped_column(String(16))  # pdf, docx, txt ...
    size_bytes: Mapped[int] = mapped_column(Integer)

    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus, native_enum=False), default=DocumentStatus.UPLOADED
    )
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    page_count: Mapped[int] = mapped_column(Integer, default=0)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False)

    chunks: Mapped[list["DocumentChunk"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )


class DocumentChunk(BaseModel):
    __tablename__ = "document_chunks"

    document_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("documents.id", ondelete="CASCADE"), index=True
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    chunk_index: Mapped[int] = mapped_column(Integer)
    page: Mapped[int] = mapped_column(Integer, default=0)
    content: Mapped[str] = mapped_column(Text)
    # Embedding vektörü JSON list olarak saklanır (DB-agnostik; pgvector'a geçiş yolu açık).
    embedding: Mapped[list[float] | None] = mapped_column(JSON, nullable=True)

    document: Mapped["Document"] = relationship(back_populates="chunks")
