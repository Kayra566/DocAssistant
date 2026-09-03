import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class SharePermission(enum.StrEnum):
    VIEW = "view"
    DOWNLOAD = "download"


class ExportFormat(enum.StrEnum):
    PDF = "pdf"
    DOCX = "docx"
    XLSX = "xlsx"
    MD = "md"


class ExportStatus(enum.StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


class ShareLink(BaseModel):
    """Doküman paylaşım bağlantısı. Ham token yalnızca oluşturma anında döner."""

    __tablename__ = "share_links"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("documents.id", ondelete="CASCADE"), index=True
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    token_hash: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    permission: Mapped[SharePermission] = mapped_column(
        Enum(SharePermission, native_enum=False), default=SharePermission.VIEW
    )
    # Doluysa bağlantı yalnızca bu e-posta ile açılabilir (email-specific paylaşım).
    email: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    last_accessed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class ActivityLog(BaseModel):
    """Kim, ne zaman, ne yaptı — organizasyon bazlı işlem geçmişi.

    Kayıtlar append-only'dir ve HMAC zinciriyle imzalanır (bkz. app.core.audit).
    """

    __tablename__ = "activity_logs"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    action: Mapped[str] = mapped_column(String(64), index=True)
    resource_type: Mapped[str] = mapped_column(String(32))
    resource_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    # Serbest biçimli ek bilgi (ör. {"filename": "rapor.pdf"}).
    meta: Mapped[dict | None] = mapped_column("meta", JSON, nullable=True)
    signature: Mapped[str | None] = mapped_column(String(64), nullable=True)
    prev_signature: Mapped[str | None] = mapped_column(String(64), nullable=True)


class DocumentComment(BaseModel):
    """Doküman üzerine yorum/not (opsiyonel sayfa referanslı)."""

    __tablename__ = "document_comments"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("documents.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    page: Mapped[int | None] = mapped_column(Integer, nullable=True)
    content: Mapped[str] = mapped_column(Text)


class ExportJob(BaseModel):
    """AI sonucunun PDF/DOCX/XLSX/MD çıktısı."""

    __tablename__ = "export_jobs"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    ai_job_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("ai_jobs.id", ondelete="CASCADE"), index=True
    )
    format: Mapped[ExportFormat] = mapped_column(Enum(ExportFormat, native_enum=False))
    status: Mapped[ExportStatus] = mapped_column(
        Enum(ExportStatus, native_enum=False), default=ExportStatus.PENDING
    )
    filename: Mapped[str] = mapped_column(String(512))
    storage_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
