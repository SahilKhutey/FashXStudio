"""Add tryon quality evaluation datasets, runs, items, ratings, and category gates (Phase 07.7)

Revision ID: 0054_add_tryon_quality_evaluation
Revises: 0053_add_tryon_cache_and_cost_controls
Create Date: 2026-11-24 11:06:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0054_add_tryon_quality_evaluation"
down_revision: str | None = "0053_add_tryon_cache_and_cost_controls"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. tryon_evaluation_datasets
    op.create_table(
        "tryon_evaluation_datasets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("version", sa.String(length=50), nullable=False),
        sa.Column("protocol_version", sa.String(length=50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("manifest_uri", sa.Text(), nullable=True),
        sa.Column("total_pairs", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="ACTIVE"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_tryon_eval_dataset_version", "tryon_evaluation_datasets", ["version"], unique=True
    )

    # 2. tryon_evaluation_runs
    op.create_table(
        "tryon_evaluation_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("run_id", sa.String(length=100), nullable=False),
        sa.Column("dataset_version", sa.String(length=50), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("provider_model", sa.String(length=64), nullable=False),
        sa.Column("provider_model_version", sa.String(length=64), nullable=False),
        sa.Column("configuration_version", sa.String(length=64), nullable=False),
        sa.Column("preprocessing_version", sa.String(length=64), nullable=False),
        sa.Column("policy_version", sa.String(length=64), nullable=False),
        sa.Column("prompt_version", sa.String(length=64), nullable=False, server_default="default"),
        sa.Column("git_commit_sha", sa.String(length=64), nullable=True),
        sa.Column(
            "spending_ceiling_usd",
            sa.Numeric(precision=10, scale=4),
            nullable=False,
            server_default="50.0000",
        ),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="RUNNING"),
        sa.Column("total_pairs", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completed_pairs", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("job_success_rate", sa.Float(), nullable=True),
        sa.Column("p95_inference_ms", sa.Integer(), nullable=True),
        sa.Column(
            "total_cost_usd",
            sa.Numeric(precision=10, scale=4),
            nullable=False,
            server_default="0.0000",
        ),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_tryon_eval_runs_run_id", "tryon_evaluation_runs", ["run_id"], unique=True)
    op.create_index("ix_tryon_eval_runs_dataset", "tryon_evaluation_runs", ["dataset_version"])

    # 3. tryon_evaluation_items
    op.create_table(
        "tryon_evaluation_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("pair_id", sa.String(length=100), nullable=False),
        sa.Column("tryon_job_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("input_validation_status", sa.String(length=32), nullable=False),
        sa.Column("job_status", sa.String(length=32), nullable=False),
        sa.Column("provider_request_id", sa.String(length=255), nullable=True),
        sa.Column("inference_duration_ms", sa.Integer(), nullable=True),
        sa.Column("end_to_end_duration_ms", sa.Integer(), nullable=True),
        sa.Column(
            "cost_usd", sa.Numeric(precision=10, scale=4), nullable=False, server_default="0.0000"
        ),
        sa.Column("output_storage_uri", sa.Text(), nullable=True),
        sa.Column("output_sha256", sa.String(length=64), nullable=True),
        sa.Column("ssim_score", sa.Float(), nullable=True),
        sa.Column("color_delta_e", sa.Float(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["run_id"], ["tryon_evaluation_runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tryon_job_id"], ["tryon_jobs.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("run_id", "pair_id", name="uq_tryon_eval_items_run_pair"),
    )
    op.create_index("ix_tryon_eval_items_run", "tryon_evaluation_items", ["run_id"])
    op.create_index("ix_tryon_eval_items_pair", "tryon_evaluation_items", ["pair_id"])

    # 4. tryon_evaluation_ratings
    op.create_table(
        "tryon_evaluation_ratings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("evaluation_item_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reviewer_id", sa.String(length=100), nullable=False),
        sa.Column("garment_preservation", sa.Integer(), nullable=False),
        sa.Column("body_alignment", sa.Integer(), nullable=False),
        sa.Column("artifact_quality", sa.Integer(), nullable=False),
        sa.Column("identity_preservation", sa.Integer(), nullable=False),
        sa.Column("visual_plausibility", sa.Integer(), nullable=False),
        sa.Column("non_misleading", sa.Integer(), nullable=False),
        sa.Column("weighted_score", sa.Float(), nullable=False),
        sa.Column("critical_issue", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("decision", sa.String(length=32), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["evaluation_item_id"], ["tryon_evaluation_items.id"], ondelete="CASCADE"
        ),
        sa.UniqueConstraint(
            "evaluation_item_id", "reviewer_id", name="uq_tryon_eval_ratings_item_reviewer"
        ),
    )
    op.create_index(
        "ix_tryon_eval_ratings_item", "tryon_evaluation_ratings", ["evaluation_item_id"]
    )
    op.create_index("ix_tryon_eval_ratings_reviewer", "tryon_evaluation_ratings", ["reviewer_id"])

    # 5. tryon_evaluation_category_gates
    op.create_table(
        "tryon_evaluation_category_gates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("sample_count", sa.Integer(), nullable=False),
        sa.Column("job_success_rate", sa.Float(), nullable=False),
        sa.Column("mean_garment_preservation", sa.Float(), nullable=False),
        sa.Column("mean_body_alignment", sa.Float(), nullable=False),
        sa.Column("mean_artifact_quality", sa.Float(), nullable=False),
        sa.Column("mean_identity_preservation", sa.Float(), nullable=False),
        sa.Column("mean_visual_plausibility", sa.Float(), nullable=False),
        sa.Column("mean_non_misleading", sa.Float(), nullable=False),
        sa.Column("reviewer_rejection_rate", sa.Float(), nullable=False),
        sa.Column("critical_misleading_count", sa.Integer(), nullable=False),
        sa.Column(
            "gate_failures",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("approved_by", sa.String(length=100), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["run_id"], ["tryon_evaluation_runs.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("category", "run_id", name="uq_tryon_eval_cat_gates_cat_run"),
    )
    op.create_index("ix_tryon_eval_cat_gates_cat", "tryon_evaluation_category_gates", ["category"])
    op.create_index("ix_tryon_eval_cat_gates_run", "tryon_evaluation_category_gates", ["run_id"])


def downgrade() -> None:
    op.drop_table("tryon_evaluation_category_gates")
    op.drop_table("tryon_evaluation_ratings")
    op.drop_table("tryon_evaluation_items")
    op.drop_table("tryon_evaluation_runs")
    op.drop_table("tryon_evaluation_datasets")
