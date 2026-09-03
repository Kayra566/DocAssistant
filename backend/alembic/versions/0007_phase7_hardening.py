"""phase 7: notifications, audit log signature chain, encrypted 2fa secret

Revision ID: 0007_phase7_hardening
Revises: 0006_phase6_collab
Create Date: 2026-08-27

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0007_phase7_hardening"
down_revision: str | None = "0006_phase6_collab"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

notification_type = sa.Enum(
    "welcome", "invite", "quota", "billing", "document", "system",
    name="notificationtype", native_enum=False,
)

# Audit log'un append-only olmasını DB seviyesinde zorlar (yalnızca Postgres).
_APPEND_ONLY_FN = """
CREATE OR REPLACE FUNCTION activity_logs_append_only()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'activity_logs is append-only';
END;
$$ LANGUAGE plpgsql;
"""


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
        "notifications",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=True),
        sa.Column("type", notification_type, nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("link", sa.String(512), nullable=True),
        sa.Column("read", sa.Boolean(), nullable=False),
        *_timestamps(),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["organization_id"], ["organizations.id"], ondelete="CASCADE"
        ),
    )
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])
    op.create_index("ix_notifications_read", "notifications", ["read"])

    op.add_column(
        "activity_logs", sa.Column("signature", sa.String(64), nullable=True)
    )
    op.add_column(
        "activity_logs", sa.Column("prev_signature", sa.String(64), nullable=True)
    )

    # TOTP secret artık şifreli saklanıyor; alan genişletiliyor.
    with op.batch_alter_table("users") as batch:
        batch.alter_column(
            "totp_secret",
            existing_type=sa.String(64),
            type_=sa.String(255),
            existing_nullable=True,
        )

    if op.get_bind().dialect.name == "postgresql":
        op.execute(_APPEND_ONLY_FN)
        op.execute(
            "CREATE TRIGGER activity_logs_no_update BEFORE UPDATE OR DELETE "
            "ON activity_logs FOR EACH ROW EXECUTE FUNCTION activity_logs_append_only()"
        )


def downgrade() -> None:
    if op.get_bind().dialect.name == "postgresql":
        op.execute("DROP TRIGGER IF EXISTS activity_logs_no_update ON activity_logs")
        op.execute("DROP FUNCTION IF EXISTS activity_logs_append_only()")

    with op.batch_alter_table("users") as batch:
        batch.alter_column(
            "totp_secret",
            existing_type=sa.String(255),
            type_=sa.String(64),
            existing_nullable=True,
        )

    op.drop_column("activity_logs", "prev_signature")
    op.drop_column("activity_logs", "signature")
    op.drop_table("notifications")
