"""add try-on result quality metadata

Revision ID: 0010_tryon_result_quality
Revises: 0009_tryon_job_runtime
"""
from alembic import op
import sqlalchemy as sa

revision = "0010_tryon_result_quality"
down_revision = "0009_tryon_job_runtime"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("tryon_artifacts", sa.Column("quality_status", sa.String(length=32), nullable=False, server_default="pending"))
    op.add_column("tryon_artifacts", sa.Column("quality_score", sa.Float(), nullable=True))
    op.add_column("tryon_artifacts", sa.Column("width", sa.Integer(), nullable=True))
    op.add_column("tryon_artifacts", sa.Column("height", sa.Integer(), nullable=True))
    op.add_column("tryon_artifacts", sa.Column("size_bytes", sa.Integer(), nullable=True))
    op.add_column("tryon_artifacts", sa.Column("content_type", sa.String(length=64), nullable=True))
    op.add_column("tryon_artifacts", sa.Column("content_sha256", sa.String(length=64), nullable=True))
    op.add_column("tryon_artifacts", sa.Column("quality_reasons", sa.JSON(), nullable=True))
    op.create_index("ix_tryon_artifacts_content_sha256", "tryon_artifacts", ["content_sha256"], unique=False)
    op.alter_column("tryon_artifacts", "quality_status", server_default=None)


def downgrade() -> None:
    op.drop_index("ix_tryon_artifacts_content_sha256", table_name="tryon_artifacts")
    for col in ("quality_reasons", "content_sha256", "content_type", "size_bytes", "height", "width", "quality_score", "quality_status"):
        op.drop_column("tryon_artifacts", col)
