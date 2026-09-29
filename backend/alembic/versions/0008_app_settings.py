"""phase 7: runtime app settings (active LLM model)

Revision ID: 0008_app_settings
Revises: 0007_phase7_hardening
Create Date: 2026-09-03

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0008_app_settings"
down_revision: str | None = "0007_phase7_hardening"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "app_settings",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("key", sa.String(64), nullable=False),
        sa.Column("value", sa.JSON(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            server_default=sa.func.now(), nullable=False,
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True),
            server_default=sa.func.now(), nullable=False,
        ),
        sa.UniqueConstraint("key", name="uq_app_setting_key"),
    )
    op.create_index("ix_app_settings_key", "app_settings", ["key"])


def downgrade() -> None:
    op.drop_table("app_settings")
