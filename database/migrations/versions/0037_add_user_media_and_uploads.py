"""Add user_media and media_uploads tables for secure photo upload pipeline

Revision ID: 0037_add_user_media_and_uploads
Revises: 0036_add_shopper_profiles
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0037_add_user_media_and_uploads"
down_revision: str | None = "0036_add_shopper_profiles"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Create user_media table
    op.create_table(
        "user_media",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("purpose", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("storage_bucket", sa.String(length=128), nullable=False),
        sa.Column("storage_key", sa.Text(), nullable=False),
        sa.Column("content_type", sa.String(length=64), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("width", sa.Integer(), nullable=False),
        sa.Column("height", sa.Integer(), nullable=False),
        sa.Column("sha256_original", sa.String(length=64), nullable=True),
        sa.Column("sha256_normalized", sa.String(length=64), nullable=False),
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
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("size_bytes > 0", name="user_media_size_positive"),
        sa.CheckConstraint("width > 0", name="user_media_width_positive"),
        sa.CheckConstraint("height > 0", name="user_media_height_positive"),
        sa.CheckConstraint(
            "purpose in ('PROFILE_PHOTO', 'VTO_PERSONAL_PHOTO')",
            name="user_media_purpose_check",
        ),
        sa.CheckConstraint(
            "status in ('AVAILABLE', 'DELETION_PENDING', 'DELETED', 'QUARANTINED')",
            name="user_media_status_check",
        ),
        sa.UniqueConstraint("storage_bucket", "storage_key", name="uq_user_media_storage_key"),
    )
    op.create_index("ix_user_media_user_id", "user_media", ["user_id"])
    op.create_index("idx_user_media_owner", "user_media", ["user_id", "created_at"])
    op.create_index("idx_user_media_status", "user_media", ["status", "updated_at"])

    # 2. Create media_uploads table
    op.create_table(
        "media_uploads",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("image_id", sa.Uuid(), nullable=False),
        sa.Column(
            "user_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("purpose", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("quarantine_key", sa.Text(), nullable=False),
        sa.Column("final_key", sa.Text(), nullable=False),
        sa.Column("declared_content_type", sa.String(length=64), nullable=False),
        sa.Column("declared_size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("min_size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("max_size_bytes", sa.BigInteger(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failure_code", sa.String(length=64), nullable=True),
        sa.CheckConstraint(
            "declared_size_bytes > 0 AND min_size_bytes > 0 AND max_size_bytes >= min_size_bytes",
            name="media_upload_size_check",
        ),
        sa.CheckConstraint(
            "status in ('PENDING_UPLOAD', 'VALIDATING', 'AVAILABLE', 'REJECTED', 'FAILED', 'EXPIRED', 'CANCELLED')",
            name="media_upload_status_check",
        ),
        sa.UniqueConstraint("image_id", name="uq_media_uploads_image_id"),
        sa.UniqueConstraint("quarantine_key", name="uq_media_uploads_quarantine_key"),
        sa.UniqueConstraint("final_key", name="uq_media_uploads_final_key"),
    )
    op.create_index("ix_media_uploads_user_id", "media_uploads", ["user_id"])
    op.create_index("idx_media_uploads_expiry", "media_uploads", ["status", "expires_at"])
    op.create_index("idx_media_uploads_user", "media_uploads", ["user_id", "created_at"])


def downgrade() -> None:
    op.drop_index("idx_media_uploads_user", table_name="media_uploads")
    op.drop_index("idx_media_uploads_expiry", table_name="media_uploads")
    op.drop_index("ix_media_uploads_user_id", table_name="media_uploads")
    op.drop_table("media_uploads")

    op.drop_index("idx_user_media_status", table_name="user_media")
    op.drop_index("idx_user_media_owner", table_name="user_media")
    op.drop_index("ix_user_media_user_id", table_name="user_media")
    op.drop_table("user_media")
