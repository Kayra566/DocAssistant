"""phase 4: ai job params/result columns

Revision ID: 0004_phase4_ai_features
Revises: 0003_phase3_rag
Create Date: 2026-08-27

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0004_phase4_ai_features"
down_revision: str | None = "0003_phase3_rag"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("ai_jobs", sa.Column("params", sa.JSON(), nullable=True))
    op.add_column("ai_jobs", sa.Column("result", sa.JSON(), nullable=True))
    op.add_column("ai_jobs", sa.Column("error", sa.Text(), nullable=True))
    op.add_column(
        "ai_jobs",
        sa.Column(
            "cache_hit", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
    )
    op.create_index("ix_ai_jobs_document_id", "ai_jobs", ["document_id"])


def downgrade() -> None:
    op.drop_index("ix_ai_jobs_document_id", table_name="ai_jobs")
    op.drop_column("ai_jobs", "cache_hit")
    op.drop_column("ai_jobs", "error")
    op.drop_column("ai_jobs", "result")
    op.drop_column("ai_jobs", "params")
