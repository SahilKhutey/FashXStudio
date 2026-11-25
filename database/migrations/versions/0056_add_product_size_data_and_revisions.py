"""Add product size data, revisions, and availability (Phase 08.1)

Revision ID: 0056_add_product_size_data_and_revisions
Revises: 0055_add_vto_fit_separation_and_size_charts
Create Date: 2026-11-25 10:45:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0056_add_product_size_data_and_revisions"
down_revision: str | None = "0055_add_vto_fit_separation_and_size_charts"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. size_system_definitions
    op.create_table(
        "size_system_definitions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(length=64), nullable=False, unique=True),
        sa.Column("system_type", sa.String(length=32), nullable=False),
        sa.Column(
            "merchant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("merchants.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("category", sa.String(length=64), nullable=False, server_default="GENERAL"),
        sa.Column("market", sa.String(length=16), nullable=False, server_default="GLOBAL"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("mapping_status", sa.String(length=32), nullable=False, server_default="UNMAPPED"),
        sa.Column("labels_json", sa.JSON(), nullable=False),
        sa.Column("display_name", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_size_system_merchant", "size_system_definitions", ["merchant_id"])

    # 2. measurement_field_definitions
    op.create_table(
        "measurement_field_definitions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(length=32), nullable=False, unique=True),
        sa.Column("display_name", sa.String(length=64), nullable=False),
        sa.Column("allowed_categories_json", sa.JSON(), nullable=False),
        sa.Column("minimum_cm", sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column("maximum_cm", sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    # 3. product_size_charts
    op.create_table(
        "product_size_charts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "merchant_product_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("merchant_products.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column(
            "merchant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("merchants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("current_revision_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("chart_status", sa.String(length=32), nullable=False, server_default="AVAILABLE"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_product_size_charts_merchant", "product_size_charts", ["merchant_id"])
    op.create_index("ix_product_size_charts_product", "product_size_charts", ["merchant_product_id"])

    # 4. size_chart_revisions
    op.create_table(
        "size_chart_revisions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "chart_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("product_size_charts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("merchant_product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("schema_version", sa.String(length=20), nullable=False, server_default="1.0"),
        sa.Column("size_system_code", sa.String(length=64), nullable=False),
        sa.Column("measurement_basis", sa.String(length=32), nullable=False),
        sa.Column("default_unit", sa.String(length=16), nullable=False, server_default="CM"),
        sa.Column("content_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("source_id", sa.String(length=128), nullable=True),
        sa.Column("source_revision", sa.String(length=128), nullable=True),
        sa.Column("source_metadata_json", sa.JSON(), nullable=True),
        sa.Column("rows_json", sa.JSON(), nullable=False),
        sa.Column("is_current", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("chart_id", "version", name="uq_size_chart_revision_version"),
    )
    op.create_index("ix_size_chart_revisions_product", "size_chart_revisions", ["merchant_product_id"])
    op.create_index("ix_size_chart_revisions_fingerprint", "size_chart_revisions", ["content_fingerprint"])
    op.create_index("ix_size_chart_revisions_chart", "size_chart_revisions", ["chart_id"])

    # 5. size_chart_rows
    op.create_table(
        "size_chart_rows",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "revision_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("size_chart_revisions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("merchant_size", sa.String(length=64), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.UniqueConstraint("revision_id", "merchant_size", name="uq_size_chart_row_label"),
    )
    op.create_index("ix_size_chart_rows_revision", "size_chart_rows", ["revision_id"])

    # 6. size_chart_measurements
    op.create_table(
        "size_chart_measurements",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "row_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("size_chart_rows.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("field_code", sa.String(length=32), nullable=False),
        sa.Column("original_value", sa.Numeric(precision=8, scale=2), nullable=False),
        sa.Column("original_unit", sa.String(length=16), nullable=False),
        sa.Column("normalized_value", sa.Numeric(precision=8, scale=2), nullable=False),
        sa.Column("normalized_unit", sa.String(length=16), nullable=False, server_default="CM"),
        sa.UniqueConstraint("row_id", "field_code", name="uq_size_chart_row_field"),
    )
    op.create_index("ix_size_chart_measurements_row", "size_chart_measurements", ["row_id"])

    # 7. inventory_snapshots
    op.create_table(
        "inventory_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("variant_id", sa.String(length=128), nullable=False),
        sa.Column("merchant_product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("size_label", sa.String(length=64), nullable=False),
        sa.Column("colour_label", sa.String(length=64), nullable=True),
        sa.Column("sku", sa.String(length=128), nullable=True),
        sa.Column("availability_status", sa.String(length=32), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("source_updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_inventory_snapshots_variant", "inventory_snapshots", ["variant_id"])
    op.create_index("ix_inventory_snapshots_product", "inventory_snapshots", ["merchant_product_id"])
    op.create_index("ix_inventory_snapshots_observed", "inventory_snapshots", ["observed_at"])

    # 8. size_chart_events
    op.create_table(
        "size_chart_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("chart_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("merchant_product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("previous_version", sa.Integer(), nullable=True),
        sa.Column("new_version", sa.Integer(), nullable=True),
        sa.Column("change_summary_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_size_chart_events_chart", "size_chart_events", ["chart_id"])
    op.create_index("ix_size_chart_events_product", "size_chart_events", ["merchant_product_id"])
    op.create_index("ix_size_chart_events_created", "size_chart_events", ["created_at"])

    # 9. size_chart_quarantine
    op.create_table(
        "size_chart_quarantine",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("merchant_product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("merchant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_id", sa.String(length=128), nullable=True),
        sa.Column("source_revision", sa.String(length=128), nullable=True),
        sa.Column("raw_payload_json", sa.JSON(), nullable=False),
        sa.Column("error_codes_json", sa.JSON(), nullable=False),
        sa.Column("review_status", sa.String(length=32), nullable=False, server_default="PENDING"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_size_chart_quarantine_product", "size_chart_quarantine", ["merchant_product_id"])
    op.create_index("ix_size_chart_quarantine_merchant", "size_chart_quarantine", ["merchant_id"])
    op.create_index("ix_size_chart_quarantine_status", "size_chart_quarantine", ["review_status"])


def downgrade() -> None:
    op.drop_table("size_chart_quarantine")
    op.drop_table("size_chart_events")
    op.drop_table("inventory_snapshots")
    op.drop_table("size_chart_measurements")
    op.drop_table("size_chart_rows")
    op.drop_table("size_chart_revisions")
    op.drop_table("product_size_charts")
    op.drop_table("measurement_field_definitions")
    op.drop_table("size_system_definitions")
