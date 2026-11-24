"""Add tryon result cache, provider usage ledger, budgets, and reservations (Phase 07.6)

Revision ID: 0053_add_tryon_cache_and_cost_controls
Revises: 0052_add_tryon_reliability_events_and_dlq
Create Date: 2026-11-24 10:45:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0053_add_tryon_cache_and_cost_controls"
down_revision: str | None = "0052_add_tryon_reliability_events_and_dlq"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. tryon_result_cache
    op.create_table(
        "tryon_result_cache",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("cache_key", sa.String(length=64), nullable=False),
        sa.Column("owner_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("canonical_product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("shopper_asset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("shopper_asset_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("garment_asset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("garment_image_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("shopper_image_sha256", sa.String(length=64), nullable=False),
        sa.Column("garment_image_sha256", sa.String(length=64), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("provider_model", sa.String(length=64), nullable=False),
        sa.Column("provider_model_version", sa.String(length=64), nullable=False),
        sa.Column("config_version", sa.String(length=64), nullable=False),
        sa.Column("preprocessing_version", sa.String(length=64), nullable=False),
        sa.Column("policy_version", sa.String(length=64), nullable=False),
        sa.Column("garment_category", sa.String(length=64), nullable=False),
        sa.Column("output_options_hash", sa.String(length=64), nullable=False),
        sa.Column("result_storage_uri", sa.Text(), nullable=False),
        sa.Column("result_storage_key", sa.Text(), nullable=True),
        sa.Column("result_sha256", sa.String(length=64), nullable=False),
        sa.Column("source_job_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="ACTIVE"),
        sa.Column("invalidation_reason", sa.Text(), nullable=True),
        sa.Column("hit_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_hit_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("metadata_expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["canonical_product_id"], ["canonical_garments.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["source_job_id"], ["tryon_jobs.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_tryon_result_cache_key", "tryon_result_cache", ["cache_key"], unique=True)
    op.create_index("ix_tryon_result_cache_owner", "tryon_result_cache", ["owner_user_id"])
    op.create_index("ix_tryon_result_cache_product", "tryon_result_cache", ["canonical_product_id"])
    op.create_index(
        "ix_tryon_result_cache_status_expires", "tryon_result_cache", ["status", "expires_at"]
    )
    op.create_index(
        "ix_tryon_result_cache_meta_expires", "tryon_result_cache", ["metadata_expires_at"]
    )

    # 2. tryon_provider_usage
    op.create_table(
        "tryon_provider_usage",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tryon_job_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("provider_model", sa.String(length=64), nullable=True),
        sa.Column("provider_request_id", sa.String(length=255), nullable=True),
        sa.Column("operation", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column(
            "units_consumed",
            sa.Numeric(precision=10, scale=4),
            nullable=False,
            server_default="1.0000",
        ),
        sa.Column(
            "unit_cost_usd",
            sa.Numeric(precision=10, scale=4),
            nullable=False,
            server_default="0.0000",
        ),
        sa.Column(
            "total_cost_usd",
            sa.Numeric(precision=10, scale=4),
            nullable=False,
            server_default="0.0000",
        ),
        sa.Column("currency", sa.String(length=8), nullable=False, server_default="USD"),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("http_status", sa.Integer(), nullable=True),
        sa.Column(
            "raw_usage_metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["tryon_job_id"], ["tryon_jobs.id"], ondelete="SET NULL"),
        sa.UniqueConstraint(
            "provider", "provider_request_id", "operation", name="uq_tryon_provider_usage_dedup"
        ),
    )
    op.create_index("ix_tryon_provider_usage_provider", "tryon_provider_usage", ["provider"])
    op.create_index("ix_tryon_provider_usage_created", "tryon_provider_usage", ["created_at"])
    op.create_index("ix_tryon_provider_usage_job", "tryon_provider_usage", ["tryon_job_id"])

    # 3. tryon_budgets
    op.create_table(
        "tryon_budgets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("scope_type", sa.String(length=32), nullable=False),
        sa.Column("scope_id", sa.String(length=128), nullable=False),
        sa.Column("period", sa.String(length=32), nullable=False),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("hard_limit_amount", sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column(
            "warn_threshold_pct",
            sa.Numeric(precision=5, scale=2),
            nullable=False,
            server_default="70.00",
        ),
        sa.Column(
            "crit_threshold_pct",
            sa.Numeric(precision=5, scale=2),
            nullable=False,
            server_default="90.00",
        ),
        sa.Column(
            "current_spend_usd",
            sa.Numeric(precision=12, scale=4),
            nullable=False,
            server_default="0.0000",
        ),
        sa.Column(
            "reserved_spend_usd",
            sa.Numeric(precision=12, scale=4),
            nullable=False,
            server_default="0.0000",
        ),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="ACTIVE"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "scope_type", "scope_id", "period", "period_start", name="uq_tryon_budgets_scope_period"
        ),
    )
    op.create_index("ix_tryon_budgets_scope", "tryon_budgets", ["scope_type", "scope_id"])
    op.create_index("ix_tryon_budgets_period", "tryon_budgets", ["period", "period_start"])

    # 4. tryon_budget_reservations
    op.create_table(
        "tryon_budget_reservations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("budget_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tryon_job_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reserved_amount_usd", sa.Numeric(precision=10, scale=4), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="RESERVED"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("committed_amount_usd", sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["budget_id"], ["tryon_budgets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tryon_job_id"], ["tryon_jobs.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_tryon_reservations_budget", "tryon_budget_reservations", ["budget_id"])
    op.create_index("ix_tryon_reservations_job", "tryon_budget_reservations", ["tryon_job_id"])
    op.create_index(
        "ix_tryon_reservations_status_expires",
        "tryon_budget_reservations",
        ["status", "expires_at"],
    )


def downgrade() -> None:
    op.drop_table("tryon_budget_reservations")
    op.drop_table("tryon_budgets")
    op.drop_table("tryon_provider_usage")
    op.drop_table("tryon_result_cache")
