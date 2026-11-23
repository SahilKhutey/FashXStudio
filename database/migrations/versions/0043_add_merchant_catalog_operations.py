"""Add merchant catalog operations, schedules, ingest run errors, audit events, and product overrides

Revision ID: 0043_add_merchant_catalog_operations
Revises: 0042_add_catalog_database_and_freshness
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0043_add_merchant_catalog_operations"
down_revision: str | None = "0042_add_catalog_database_and_freshness"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Extend catalog_sources with operational controls
    op.add_column(
        "catalog_sources",
        sa.Column("is_enabled", sa.Boolean(), server_default=sa.true(), nullable=False),
    )
    op.add_column(
        "catalog_sources",
        sa.Column("operational_status", sa.String(length=32), server_default="ENABLED", nullable=False),
    )

    # 2. Create catalog_source_schedules
    op.create_table(
        "catalog_source_schedules",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("source_id", sa.Uuid(), nullable=False),
        sa.Column("merchant_id", sa.Uuid(), nullable=False),
        sa.Column("enabled", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("sync_mode", sa.String(length=32), server_default="INCREMENTAL", nullable=False),
        sa.Column("interval_minutes", sa.Integer(), server_default="60", nullable=False),
        sa.Column("cron_expression", sa.String(length=100), nullable=True),
        sa.Column("timezone", sa.String(length=64), server_default="UTC", nullable=False),
        sa.Column("last_scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_id"], ["catalog_sources.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source_id", name="uq_source_schedules_source"),
    )
    op.create_index(
        "ix_source_schedules_merchant",
        "catalog_source_schedules",
        ["merchant_id"],
        unique=False,
    )
    op.create_index(
        "ix_source_schedules_next_run",
        "catalog_source_schedules",
        ["next_run_at"],
        unique=False,
    )

    # 3. Create ingest_run_errors
    op.create_table(
        "ingest_run_errors",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("ingest_run_id", sa.Uuid(), nullable=False),
        sa.Column("source_id", sa.Uuid(), nullable=False),
        sa.Column("merchant_id", sa.Uuid(), nullable=True),
        sa.Column("error_code", sa.String(length=80), nullable=False),
        sa.Column("error_category", sa.String(length=40), server_default="INTERNAL", nullable=False),
        sa.Column("failed_stage", sa.String(length=40), server_default="FETCH", nullable=False),
        sa.Column("source_product_reference", sa.String(length=255), nullable=True),
        sa.Column("safe_error_message", sa.Text(), nullable=False),
        sa.Column("retryable", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("attempt_number", sa.Integer(), server_default="1", nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["ingest_run_id"], ["ingest_runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchants.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["source_id"], ["catalog_sources.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_ingest_run_errors_run",
        "ingest_run_errors",
        ["ingest_run_id"],
        unique=False,
    )
    op.create_index(
        "ix_ingest_run_errors_source",
        "ingest_run_errors",
        ["source_id"],
        unique=False,
    )
    op.create_index(
        "ix_ingest_run_errors_category",
        "ingest_run_errors",
        ["error_category"],
        unique=False,
    )

    # 4. Create catalog_source_audit_events
    op.create_table(
        "catalog_source_audit_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("actor_id", sa.Uuid(), nullable=True),
        sa.Column("actor_role", sa.String(length=40), server_default="SYSTEM", nullable=False),
        sa.Column("merchant_id", sa.Uuid(), nullable=True),
        sa.Column("source_id", sa.Uuid(), nullable=True),
        sa.Column("entity_type", sa.String(length=50), nullable=False),
        sa.Column("entity_id", sa.String(length=255), nullable=True),
        sa.Column("action", sa.String(length=80), nullable=False),
        sa.Column("reason_code", sa.String(length=80), nullable=True),
        sa.Column("safe_change_summary", sa.JSON(), server_default="{}", nullable=False),
        sa.Column("request_id", sa.String(length=128), nullable=True),
        sa.Column("outcome", sa.String(length=30), server_default="SUCCESS", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchants.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["source_id"], ["catalog_sources.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_catalog_source_audit_merchant",
        "catalog_source_audit_events",
        ["merchant_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_catalog_source_audit_source",
        "catalog_source_audit_events",
        ["source_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_catalog_source_audit_actor",
        "catalog_source_audit_events",
        ["actor_id", "created_at"],
        unique=False,
    )

    # 5. Create merchant_product_overrides
    op.create_table(
        "merchant_product_overrides",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("merchant_id", sa.Uuid(), nullable=False),
        sa.Column("merchant_product_id", sa.Uuid(), nullable=False),
        sa.Column("field_name", sa.String(length=64), nullable=False),
        sa.Column("override_value", sa.JSON(), nullable=False),
        sa.Column("previous_value", sa.JSON(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["merchant_product_id"], ["merchant_products.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "merchant_id",
            "merchant_product_id",
            "field_name",
            name="uq_merchant_prod_override_field",
        ),
    )
    op.create_index(
        "ix_merchant_prod_overrides_lookup",
        "merchant_product_overrides",
        ["merchant_id", "merchant_product_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_merchant_prod_overrides_lookup", table_name="merchant_product_overrides")
    op.drop_table("merchant_product_overrides")

    op.drop_index("ix_catalog_source_audit_actor", table_name="catalog_source_audit_events")
    op.drop_index("ix_catalog_source_audit_source", table_name="catalog_source_audit_events")
    op.drop_index("ix_catalog_source_audit_merchant", table_name="catalog_source_audit_events")
    op.drop_table("catalog_source_audit_events")

    op.drop_index("ix_ingest_run_errors_category", table_name="ingest_run_errors")
    op.drop_index("ix_ingest_run_errors_source", table_name="ingest_run_errors")
    op.drop_index("ix_ingest_run_errors_run", table_name="ingest_run_errors")
    op.drop_table("ingest_run_errors")

    op.drop_index("ix_source_schedules_next_run", table_name="catalog_source_schedules")
    op.drop_index("ix_source_schedules_merchant", table_name="catalog_source_schedules")
    op.drop_table("catalog_source_schedules")

    op.drop_column("catalog_sources", "operational_status")
    op.drop_column("catalog_sources", "is_enabled")
