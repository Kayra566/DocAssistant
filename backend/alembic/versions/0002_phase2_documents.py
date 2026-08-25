"""phase 2: documents and chunks

Revision ID: 0002_phase2_documents
Revises: 0001_phase1_auth
Create Date: 2026-08-25

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0002_phase2_documents"
down_revision: str | None = "0001_phase1_auth"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

status_enum = sa.Enum(
    "UPLOADED",
    "PROCESSING",
    "READY",
    "FAILED",
    name="documentstatus",
    native_enum=False,
)


def _timestamps() -> list[sa.Column]:
    return [
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    ]


def upgrade() -> None:
    op.create_table(
        "documents",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=True),
        sa.Column("filename", sa.String(512), nullable=False),
        sa.Column("storage_key", sa.String(512), nullable=False),
        sa.Column("mime_type", sa.String(128), nullable=False),
        sa.Column("file_type", sa.String(16), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("status", status_enum, nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("page_count", sa.Integer(), nullable=False),
        sa.Column("chunk_count", sa.Integer(), nullable=False),
        sa.Column("is_favorite", sa.Boolean(), nullable=False),
        *_timestamps(),
        sa.ForeignKeyConstraint(
            ["organization_id"], ["organizations.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index(
        "ix_documents_organization_id", "documents", ["organization_id"]
    )

    op.create_table(
        "document_chunks",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("page", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding", sa.JSON(), nullable=True),
        *_timestamps(),
        sa.ForeignKeyConstraint(
            ["document_id"], ["documents.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"], ["organizations.id"], ondelete="CASCADE"
        ),
    )
    op.create_index(
        "ix_document_chunks_document_id", "document_chunks", ["document_id"]
    )
    op.create_index(
        "ix_document_chunks_organization_id",
        "document_chunks",
        ["organization_id"],
    )


def downgrade() -> None:
    op.drop_table("document_chunks")
    op.drop_table("documents")
