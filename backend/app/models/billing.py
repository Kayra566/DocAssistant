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
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel
from app.models.enums import Plan


class SubscriptionStatus(enum.StrEnum):
    ACTIVE = "active"
    TRIALING = "trialing"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    INCOMPLETE = "incomplete"


class UsageMetric(enum.StrEnum):
    AI_REQUESTS = "ai_requests"
    AI_TOKENS = "ai_tokens"
    DOCUMENTS = "documents"
    STORAGE_BYTES = "storage_bytes"


class Subscription(BaseModel):
    __tablename__ = "subscriptions"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id", ondelete="CASCADE"), unique=True, index=True
    )
    plan: Mapped[Plan] = mapped_column(Enum(Plan, native_enum=False), default=Plan.FREE)
    status: Mapped[SubscriptionStatus] = mapped_column(
        Enum(SubscriptionStatus, native_enum=False), default=SubscriptionStatus.ACTIVE
    )
    provider_customer_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True, index=True
    )
    provider_subscription_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True, unique=True, index=True
    )
    current_period_end: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    cancel_at_period_end: Mapped[bool] = mapped_column(Boolean, default=False)


class UsageRecord(BaseModel):
    """Aylık kullanım sayacı. period_start ayın ilk günüdür (otomatik reset)."""

    __tablename__ = "usage_records"
    __table_args__ = (
        UniqueConstraint(
            "organization_id", "period_start", "metric", name="uq_usage_period_metric"
        ),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    metric: Mapped[UsageMetric] = mapped_column(
        Enum(UsageMetric, native_enum=False)
    )
    value: Mapped[int] = mapped_column(Integer, default=0)


class WebhookEvent(BaseModel):
    """Ödeme sağlayıcısı event log'u — idempotency için."""

    __tablename__ = "webhook_events"

    event_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    type: Mapped[str] = mapped_column(String(128), index=True)
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    error: Mapped[str | None] = mapped_column(String(1000), nullable=True)
