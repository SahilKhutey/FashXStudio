"""tryon provider tracking and usage cost accounting

Revision ID: 0017_tryon_provider_tracking
Revises: 0016_media_objects
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0017_tryon_provider_tracking"
down_revision: str | None = "0016_media_objects"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("tryon_jobs", sa.Column("provider", sa.Text(), nullable=True))
    op.add_column("tryon_jobs", sa.Column("provider_job_id", sa.Text(), nullable=True))
    op.create_table(
        "tryon_usage",
        sa.Column("id", sa.Uuid(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("provider", sa.Text(), nullable=False),
        sa.Column("model", sa.Text(), nullable=False),
        sa.Column("outcome", sa.Text(), nullable=False),
        sa.Column("error_code", sa.Text(), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("cost_usd_est", sa.Numeric(10, 4), nullable=True),
    )
    op.create_index("ix_tryon_usage_created", "tryon_usage", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_tryon_usage_created", table_name="tryon_usage")
    op.drop_table("tryon_usage")
    op.drop_column("tryon_jobs", "provider_job_id")
    op.drop_column("tryon_jobs", "provider")
