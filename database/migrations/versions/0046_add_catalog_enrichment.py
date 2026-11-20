"""Add catalog product enrichment, evidence, reviews and model run tables

Revision ID: 0046_add_catalog_enrichment
Revises: 0045_add_fashion_taxonomy
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0046_add_catalog_enrichment"
down_revision: str | None = "0045_add_fashion_taxonomy"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Create product_enrichment_runs
    op.create_table(
        "product_enrichment_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("source_revision", sa.String(length=64), nullable=True),
        sa.Column("taxonomy_version", sa.String(length=32), nullable=False),
        sa.Column("enrichment_version", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), server_default="QUEUED", nullable=False),
        sa.Column("attempt_number", sa.Integer(), server_default="1", nullable=False),
        sa.Column("idempotency_key", sa.String(length=64), nullable=True),
        sa.Column("request_id", sa.String(length=64), nullable=True),
        sa.Column("error_code", sa.String(length=64), nullable=True),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_product_enrichment_runs_product_id",
        "product_enrichment_runs",
        ["product_id"],
        unique=False,
    )
    op.create_index(
        "ix_product_enrichment_runs_idempotency_key",
        "product_enrichment_runs",
        ["idempotency_key"],
        unique=False,
    )

    # 2. Create product_enrichment_results
    op.create_table(
        "product_enrichment_results",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("taxonomy_version", sa.String(length=32), nullable=False),
        sa.Column("enrichment_version", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("category_id", sa.String(length=64), nullable=True),
        sa.Column("garment_type", sa.String(length=64), nullable=True),
        sa.Column("summary_json", sa.JSON(), server_default="{}", nullable=False),
        sa.Column("is_current", sa.Boolean(), server_default="true", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["run_id"], ["product_enrichment_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_product_enrichment_results_run_id",
        "product_enrichment_results",
        ["run_id"],
        unique=False,
    )
    op.create_index(
        "ix_product_enrichment_results_product_id",
        "product_enrichment_results",
        ["product_id"],
        unique=False,
    )
    op.create_index(
        "ix_product_enrichment_current",
        "product_enrichment_results",
        ["product_id", "is_current"],
        unique=False,
    )

    # 3. Create product_attribute_evidence
    op.create_table(
        "product_attribute_evidence",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("attribute_id", sa.String(length=64), nullable=False),
        sa.Column("evidence_type", sa.String(length=32), nullable=False),
        sa.Column("source_record_id", sa.String(length=128), nullable=False),
        sa.Column("source_revision", sa.String(length=64), nullable=True),
        sa.Column("asset_id", sa.String(length=128), nullable=True),
        sa.Column("evidence_text", sa.Text(), nullable=True),
        sa.Column("evidence_hash", sa.String(length=64), nullable=True),
        sa.Column("start_offset", sa.Integer(), nullable=True),
        sa.Column("end_offset", sa.Integer(), nullable=True),
        sa.Column("extraction_method", sa.String(length=64), nullable=True),
        sa.Column("model_id", sa.String(length=64), nullable=True),
        sa.Column("model_version", sa.String(length=32), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_product_attribute_evidence_product_id",
        "product_attribute_evidence",
        ["product_id"],
        unique=False,
    )
    op.create_index(
        "ix_product_attribute_evidence_attribute_id",
        "product_attribute_evidence",
        ["attribute_id"],
        unique=False,
    )
    op.create_index(
        "ix_product_attr_evidence_lookup",
        "product_attribute_evidence",
        ["product_id", "attribute_id"],
        unique=False,
    )

    # 4. Create product_attribute_reviews
    op.create_table(
        "product_attribute_reviews",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("merchant_id", sa.Uuid(), nullable=False),
        sa.Column("attribute_id", sa.String(length=64), nullable=False),
        sa.Column("proposed_value", sa.Text(), nullable=True),
        sa.Column("current_value", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), server_default="PENDING", nullable=False),
        sa.Column("confidence", sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column("flags_json", sa.JSON(), server_default="[]", nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("assigned_to", sa.String(length=64), nullable=True),
        sa.Column("reviewed_by", sa.String(length=64), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_product_attribute_reviews_product_id",
        "product_attribute_reviews",
        ["product_id"],
        unique=False,
    )
    op.create_index(
        "ix_product_attribute_reviews_merchant_id",
        "product_attribute_reviews",
        ["merchant_id"],
        unique=False,
    )
    op.create_index(
        "ix_product_attr_reviews_tenant",
        "product_attribute_reviews",
        ["merchant_id", "status"],
        unique=False,
    )

    # 5. Create product_attribute_review_events
    op.create_table(
        "product_attribute_review_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("review_id", sa.Uuid(), nullable=False),
        sa.Column("actor_id", sa.String(length=64), nullable=False),
        sa.Column("action", sa.String(length=32), nullable=False),
        sa.Column("previous_value", sa.Text(), nullable=True),
        sa.Column("new_value", sa.Text(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["review_id"], ["product_attribute_reviews.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_product_attribute_review_events_review_id",
        "product_attribute_review_events",
        ["review_id"],
        unique=False,
    )

    # 6. Create product_enrichment_model_runs
    op.create_table(
        "product_enrichment_model_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("model_id", sa.String(length=64), nullable=False),
        sa.Column("model_version", sa.String(length=32), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=False),
        sa.Column("prompt_tokens", sa.Integer(), nullable=True),
        sa.Column("completion_tokens", sa.Integer(), nullable=True),
        sa.Column("cost_usd", sa.Numeric(precision=8, scale=6), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["run_id"], ["product_enrichment_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_product_enrichment_model_runs_run_id",
        "product_enrichment_model_runs",
        ["run_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_table("product_enrichment_model_runs")
    op.drop_table("product_attribute_review_events")
    op.drop_table("product_attribute_reviews")
    op.drop_table("product_attribute_evidence")
    op.drop_table("product_enrichment_results")
    op.drop_table("product_enrichment_runs")
