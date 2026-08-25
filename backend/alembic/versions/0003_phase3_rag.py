"""phase 3: ai jobs, conversations, chat messages

Revision ID: 0003_phase3_rag
Revises: 0002_phase2_documents
Create Date: 2026-08-25

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0003_phase3_rag"
down_revision: str | None = "0002_phase2_documents"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

job_type = sa.Enum(
    "chat", "summary", "keypoints", "quiz", "translate", "extract", "compare",
    name="aijobtype", native_enum=False,
)
job_status = sa.Enum(
    "pending", "running", "done", "failed", name="aijobstatus", native_enum=False
)


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
        "ai_jobs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("document_id", sa.Uuid(), nullable=True),
        sa.Column("type", job_type, nullable=False),
        sa.Column("status", job_status, nullable=False),
        sa.Column("tokens_used", sa.Integer(), nullable=False),
        sa.Column("cost", sa.Numeric(10, 6), nullable=False),
        *_timestamps(),
        sa.ForeignKeyConstraint(
            ["organization_id"], ["organizations.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(
            ["document_id"], ["documents.id"], ondelete="SET NULL"
        ),
    )
    op.create_index("ix_ai_jobs_organization_id", "ai_jobs", ["organization_id"])

    op.create_table(
        "conversations",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("title", sa.String(255), nullable=False),
        *_timestamps(),
        sa.ForeignKeyConstraint(
            ["organization_id"], ["organizations.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["document_id"], ["documents.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index(
        "ix_conversations_organization_id", "conversations", ["organization_id"]
    )
    op.create_index(
        "ix_conversations_document_id", "conversations", ["document_id"]
    )

    op.create_table(
        "chat_messages",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("conversation_id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("role", sa.String(16), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("citations", sa.JSON(), nullable=True),
        sa.Column("tokens", sa.Integer(), nullable=False),
        *_timestamps(),
        sa.ForeignKeyConstraint(
            ["conversation_id"], ["conversations.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"], ["organizations.id"], ondelete="CASCADE"
        ),
    )
    op.create_index(
        "ix_chat_messages_conversation_id", "chat_messages", ["conversation_id"]
    )
    op.create_index(
        "ix_chat_messages_organization_id", "chat_messages", ["organization_id"]
    )


def downgrade() -> None:
    op.drop_table("chat_messages")
    op.drop_table("conversations")
    op.drop_table("ai_jobs")
