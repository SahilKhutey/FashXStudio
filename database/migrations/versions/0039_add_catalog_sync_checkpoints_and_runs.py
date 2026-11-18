"""Add catalog sync checkpoints and sync runs

Revision ID: 0039_add_catalog_sync_checkpoints_and_runs
Revises: 0038_add_catalog_authorization_and_sources
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0039_add_catalog_sync_checkpoints_and_runs"
down_revision: str | None = "0038_add_catalog_authorization_and_sources"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Create catalog_sync_checkpoints table
    op.create_table(
        "catalog_sync_checkpoints",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "source_id",
            sa.Uuid(),
            sa.ForeignKey("catalog_sources.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("checkpoint_type", sa.String(length=30), nullable=False),
        sa.Column("cursor_data", sa.JSON(), nullable=True),
        sa.Column("watermark", sa.DateTime(timezone=True), nullable=True),
        sa.Column("provider_version", sa.String(length=255), nullable=True),
        sa.Column("last_success_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("source_id", "checkpoint_type", name="uq_sync_checkpoint_source_type"),
    )
    op.create_index(
        "ix_sync_checkpoint_source",
        "catalog_sync_checkpoints",
        ["source_id"],
    )

    # 2. Create catalog_sync_runs table
    op.create_table(
        "catalog_sync_runs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "source_id",
            sa.Uuid(),
            sa.ForeignKey("catalog_sources.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("mode", sa.String(length=20), nullable=False),
        sa.Column(
            "status",
            sa.String(length=30),
            server_default="running",
            nullable=False,
        ),
        sa.Column("snapshot_id", sa.String(length=255), nullable=True),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("pages_fetched", sa.Integer(), server_default="0", nullable=False),
        sa.Column("products_seen", sa.Integer(), server_default="0", nullable=False),
        sa.Column("products_inserted", sa.Integer(), server_default="0", nullable=False),
        sa.Column("products_updated", sa.Integer(), server_default="0", nullable=False),
        sa.Column("products_rejected", sa.Integer(), server_default="0", nullable=False),
        sa.Column("error_code", sa.String(length=80), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_sync_runs_source",
        "catalog_sync_runs",
        ["source_id", "started_at"],
    )
    op.create_index(
        "ix_sync_runs_status",
        "catalog_sync_runs",
        ["status"],
    )


def downgrade() -> None:
    op.drop_index("ix_sync_runs_status", table_name="catalog_sync_runs")
    op.drop_index("ix_sync_runs_source", table_name="catalog_sync_runs")
    op.drop_table("catalog_sync_runs")

    op.drop_index("ix_sync_checkpoint_source", table_name="catalog_sync_checkpoints")
    op.drop_table("catalog_sync_checkpoints")
