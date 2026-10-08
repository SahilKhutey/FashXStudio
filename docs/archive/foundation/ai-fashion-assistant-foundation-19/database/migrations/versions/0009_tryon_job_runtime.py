"""add try-on runtime metadata and locking

Revision ID: 0009_tryon_job_runtime
Revises: 0008_catalog_runtime
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0009_tryon_job_runtime"
down_revision: str | None = "0008_catalog_runtime"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("tryon_jobs") as batch:
        batch.add_column(sa.Column("photo_version", sa.Integer(), nullable=False, server_default="1"))
        batch.add_column(sa.Column("garment_version", sa.Integer(), nullable=False, server_default="1"))
        batch.add_column(sa.Column("configuration_hash", sa.String(length=128), nullable=False, server_default="default"))
        batch.add_column(sa.Column("queue_name", sa.String(length=128), nullable=False, server_default="tryon-jobs"))
        batch.add_column(sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"))
        batch.add_column(sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True))
        batch.add_column(sa.Column("provider_job_id", sa.String(length=255), nullable=True))
        batch.add_column(sa.Column("cancel_requested", sa.Boolean(), nullable=False, server_default=sa.false()))
        batch.add_column(sa.Column("last_error", sa.Text(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("tryon_jobs") as batch:
        for name in [
            "last_error",
            "cancel_requested",
            "provider_job_id",
            "locked_at",
            "attempt_count",
            "queue_name",
            "configuration_hash",
            "garment_version",
            "photo_version",
        ]:
            batch.drop_column(name)
