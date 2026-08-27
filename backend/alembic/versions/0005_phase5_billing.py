"""phase 5: subscriptions, usage records, webhook events

Revision ID: 0005_phase5_billing
Revises: 0004_phase4_ai_features
Create Date: 2026-08-27

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0005_phase5_billing"
down_revision: str | None = "0004_phase4_ai_features"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

subscription_status = sa.Enum(
    "active", "trialing", "past_due", "canceled", "incomplete",
    name="subscriptionstatus", native_enum=False,
)
usage_metric = sa.Enum(
    "ai_requests", "ai_tokens", "documents", "storage_bytes",
    name="usagemetric", native_enum=False,
)
plan_enum = sa.Enum("free", "pro", "business", name="plan", native_enum=False)


def _timestamps() -> list[sa.Column]:
    return [
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            server_default=sa.func.now(), nullable=False,
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True),
            server_default=sa.func.now(), nullable=False,
        ),
    ]


def upgrade() -> None:
    op.create_table(
        "subscriptions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("plan", plan_enum, nullable=False),
        sa.Column("status", subscription_status, nullable=False),
        sa.Column("provider_customer_id", sa.String(255), nullable=True),
        sa.Column("provider_subscription_id", sa.String(255), nullable=True),
        sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancel_at_period_end", sa.Boolean(), nullable=False),
        *_timestamps(),
        sa.ForeignKeyConstraint(
            ["organization_id"], ["organizations.id"], ondelete="CASCADE"
        ),
        sa.UniqueConstraint("organization_id", name="uq_subscription_org"),
        sa.UniqueConstraint(
            "provider_subscription_id", name="uq_subscription_provider_id"
        ),
    )
    op.create_index(
        "ix_subscriptions_organization_id", "subscriptions", ["organization_id"]
    )
    op.create_index(
        "ix_subscriptions_provider_customer_id",
        "subscriptions",
        ["provider_customer_id"],
    )

    op.create_table(
        "usage_records",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("metric", usage_metric, nullable=False),
        sa.Column("value", sa.Integer(), nullable=False),
        *_timestamps(),
        sa.ForeignKeyConstraint(
            ["organization_id"], ["organizations.id"], ondelete="CASCADE"
        ),
        sa.UniqueConstraint(
            "organization_id", "period_start", "metric",
            name="uq_usage_period_metric",
        ),
    )
    op.create_index(
        "ix_usage_records_organization_id", "usage_records", ["organization_id"]
    )
    op.create_index("ix_usage_records_period_start", "usage_records", ["period_start"])

    op.create_table(
        "webhook_events",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("event_id", sa.String(255), nullable=False),
        sa.Column("type", sa.String(128), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error", sa.String(1000), nullable=True),
        *_timestamps(),
        sa.UniqueConstraint("event_id", name="uq_webhook_event_id"),
    )
    op.create_index("ix_webhook_events_event_id", "webhook_events", ["event_id"])
    op.create_index("ix_webhook_events_type", "webhook_events", ["type"])


def downgrade() -> None:
    op.drop_table("webhook_events")
    op.drop_table("usage_records")
    op.drop_table("subscriptions")
