"""Add catalog ingestion quarantine and ingest run extensions

Revision ID: 0040_add_catalog_ingestion_quarantine
Revises: 0039_add_catalog_sync_checkpoints_and_runs
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0040_add_catalog_ingestion_quarantine"
down_revision: str | None = "0039_add_catalog_sync_checkpoints_and_runs"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Add columns to ingest_runs
    op.add_column(
        "ingest_runs",
        sa.Column(
            "merchant_id",
            sa.Uuid(),
            sa.ForeignKey("merchants.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "ingest_runs",
        sa.Column("sync_mode", sa.String(length=20), nullable=True),
    )
    op.add_column(
        "ingest_runs",
        sa.Column("correlation_id", sa.String(length=64), nullable=True),
    )
    op.create_index(
        "ix_ingest_runs_merchant",
        "ingest_runs",
        ["merchant_id"],
    )

    # 2. Create catalog_ingestion_quarantine table
    op.create_table(
        "catalog_ingestion_quarantine",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "ingest_run_id",
            sa.Uuid(),
            sa.ForeignKey("ingest_runs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "source_id",
            sa.Uuid(),
            sa.ForeignKey("catalog_sources.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("source_product_id", sa.String(length=255), nullable=True),
        sa.Column("reason_code", sa.String(length=100), nullable=False),
        sa.Column("field_name", sa.String(length=100), nullable=True),
        sa.Column("safe_record_reference", sa.JSON(), nullable=True),
        sa.Column("record_hash", sa.String(length=64), nullable=True),
        sa.Column(
            "status",
            sa.String(length=30),
            server_default="PENDING",
            nullable=False,
        ),
        sa.Column(
            "first_seen_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "last_seen_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolution_note", sa.String(length=1024), nullable=True),
        sa.UniqueConstraint(
            "source_id",
            "source_product_id",
            "reason_code",
            name="uq_quarantine_source_prod_reason",
        ),
    )
    op.create_index(
        "ix_ingestion_quarantine_source",
        "catalog_ingestion_quarantine",
        ["source_id", "status"],
    )
    op.create_index(
        "ix_ingestion_quarantine_run",
        "catalog_ingestion_quarantine",
        ["ingest_run_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_ingestion_quarantine_run", table_name="catalog_ingestion_quarantine")
    op.drop_index("ix_ingestion_quarantine_source", table_name="catalog_ingestion_quarantine")
    op.drop_table("catalog_ingestion_quarantine")

    op.drop_index("ix_ingest_runs_merchant", table_name="ingest_runs")
    op.drop_column("ingest_runs", "correlation_id")
    op.drop_column("ingest_runs", "sync_mode")
    op.drop_column("ingest_runs", "merchant_id")
