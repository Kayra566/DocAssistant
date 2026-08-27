"""phase 6: share links, activity logs, comments, export jobs

Revision ID: 0006_phase6_collab
Revises: 0005_phase5_billing
Create Date: 2026-08-27

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0006_phase6_collab"
down_revision: str | None = "0005_phase5_billing"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

share_permission = sa.Enum(
    "view", "download", name="sharepermission", native_enum=False
)
export_format = sa.Enum("pdf", "docx", "xlsx", "md", name="exportformat", native_enum=False)
export_status = sa.Enum(
    "pending", "running", "done", "failed", name="exportstatus", native_enum=False
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
        "share_links",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column("token_hash", sa.String(128), nullable=False),
        sa.Column("permission", share_permission, nullable=False),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False),
        sa.Column("view_count", sa.Integer(), nullable=False),
        sa.Column("last_accessed_at", sa.DateTime(timezone=True), nullable=True),
        *_timestamps(),
        sa.ForeignKeyConstraint(
            ["organization_id"], ["organizations.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("token_hash", name="uq_share_link_token"),
    )
    op.create_index("ix_share_links_organization_id", "share_links", ["organization_id"])
    op.create_index("ix_share_links_document_id", "share_links", ["document_id"])
    op.create_index("ix_share_links_token_hash", "share_links", ["token_hash"])
    op.create_index("ix_share_links_email", "share_links", ["email"])

    op.create_table(
        "activity_logs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("resource_type", sa.String(32), nullable=False),
        sa.Column("resource_id", sa.Uuid(), nullable=True),
        sa.Column("meta", sa.JSON(), nullable=True),
        *_timestamps(),
        sa.ForeignKeyConstraint(
            ["organization_id"], ["organizations.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index(
        "ix_activity_logs_organization_id", "activity_logs", ["organization_id"]
    )
    op.create_index("ix_activity_logs_action", "activity_logs", ["action"])

    op.create_table(
        "document_comments",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("page", sa.Integer(), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        *_timestamps(),
        sa.ForeignKeyConstraint(
            ["organization_id"], ["organizations.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index(
        "ix_document_comments_organization_id", "document_comments", ["organization_id"]
    )
    op.create_index(
        "ix_document_comments_document_id", "document_comments", ["document_id"]
    )

    op.create_table(
        "export_jobs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("ai_job_id", sa.Uuid(), nullable=False),
        sa.Column("format", export_format, nullable=False),
        sa.Column("status", export_status, nullable=False),
        sa.Column("filename", sa.String(512), nullable=False),
        sa.Column("storage_key", sa.String(512), nullable=True),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        *_timestamps(),
        sa.ForeignKeyConstraint(
            ["organization_id"], ["organizations.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["ai_job_id"], ["ai_jobs.id"], ondelete="CASCADE"),
    )
    op.create_index(
        "ix_export_jobs_organization_id", "export_jobs", ["organization_id"]
    )
    op.create_index("ix_export_jobs_ai_job_id", "export_jobs", ["ai_job_id"])


def downgrade() -> None:
    op.drop_table("export_jobs")
    op.drop_table("document_comments")
    op.drop_table("activity_logs")
    op.drop_table("share_links")
