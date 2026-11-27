"""Add Phase 08.3 fit recommendation snapshots, feedback fields, evidence, candidates, and evaluation tables

Revision ID: 0058_add_fit_recommendation_snapshot_feedback_eval
Revises: 0057_add_shopper_fit_profile_and_history
Create Date: 2026-11-26 10:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0058_add_fit_recommendation_snapshot_feedback_eval"
down_revision: str | None = "0057_add_shopper_fit_profile_and_history"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Extend fit_recommendations with Phase 08.3 snapshot/provenance columns
    with op.batch_alter_table("fit_recommendations") as b:
        b.add_column(
            sa.Column(
                "merchant_id",
                sa.UUID(),
                sa.ForeignKey("merchants.id", ondelete="SET NULL"),
                nullable=True,
            )
        )
        b.add_column(
            sa.Column(
                "merchant_product_id",
                sa.UUID(),
                sa.ForeignKey("merchant_products.id", ondelete="SET NULL"),
                nullable=True,
            )
        )
        b.add_column(sa.Column("variant_id", sa.String(length=128), nullable=True))
        b.add_column(
            sa.Column(
                "size_chart_id",
                sa.UUID(),
                sa.ForeignKey("product_size_charts.id", ondelete="SET NULL"),
                nullable=True,
            )
        )
        b.add_column(sa.Column("size_chart_revision", sa.Integer(), nullable=True))
        b.add_column(sa.Column("shopper_measurement_revision", sa.Integer(), nullable=True))
        b.add_column(sa.Column("category_policy_version", sa.String(length=32), nullable=True))
        b.add_column(sa.Column("fit_algorithm_version", sa.String(length=32), nullable=True))
        b.add_column(sa.Column("fit_preference_revision", sa.Integer(), nullable=True))
        b.add_column(sa.Column("source_permission_revision", sa.Integer(), nullable=True))
        b.add_column(sa.Column("recommendation_status", sa.String(length=40), nullable=True))
        b.add_column(
            sa.Column(
                "reason_codes_json",
                sa.JSON(),
                nullable=False,
                server_default="[]",
            )
        )
        b.add_column(
            sa.Column(
                "internal_confidence_score",
                sa.Numeric(precision=5, scale=3),
                nullable=True,
            )
        )
        b.add_column(sa.Column("invalidation_reason", sa.String(length=64), nullable=True))
        b.add_column(sa.Column("invalidated_at", sa.DateTime(timezone=True), nullable=True))
        b.add_column(sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True))
        b.alter_column(
            "outcome",
            existing_type=sa.String(length=32),
            type_=sa.String(length=40),
            existing_nullable=False,
        )
        b.alter_column(
            "recommended_size",
            existing_type=sa.String(length=32),
            type_=sa.String(length=64),
            existing_nullable=True,
        )

    op.create_index("ix_fit_recommendations_offer", "fit_recommendations", ["merchant_offer_id"])
    op.create_index("ix_fit_recommendations_chart", "fit_recommendations", ["size_chart_id"])
    op.create_index("ix_fit_recommendations_valid", "fit_recommendations", ["user_id", "is_valid"])

    # 2. Extend fit_feedback for recommendation-linked feedback & triage
    with op.batch_alter_table("fit_feedback") as b:
        b.alter_column("brand_id", existing_type=sa.UUID(), nullable=True)
        b.add_column(
            sa.Column(
                "recommendation_id",
                sa.UUID(),
                sa.ForeignKey("fit_recommendations.id", ondelete="CASCADE"),
                nullable=True,
            )
        )
        b.add_column(
            sa.Column(
                "merchant_id",
                sa.UUID(),
                sa.ForeignKey("merchants.id", ondelete="SET NULL"),
                nullable=True,
            )
        )
        b.add_column(
            sa.Column(
                "merchant_offer_id",
                sa.UUID(),
                sa.ForeignKey("merchant_offers.id", ondelete="SET NULL"),
                nullable=True,
            )
        )
        b.add_column(
            sa.Column(
                "size_chart_id",
                sa.UUID(),
                sa.ForeignKey("product_size_charts.id", ondelete="SET NULL"),
                nullable=True,
            )
        )
        b.add_column(sa.Column("size_chart_revision", sa.Integer(), nullable=True))
        b.add_column(sa.Column("reason", sa.String(length=64), nullable=True))
        b.add_column(
            sa.Column(
                "purchase_status",
                sa.String(length=32),
                nullable=False,
                server_default="UNKNOWN",
            )
        )
        b.add_column(
            sa.Column(
                "tried_on",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("false"),
            )
        )
        b.add_column(sa.Column("kept_item", sa.Boolean(), nullable=True))
        b.add_column(
            sa.Column(
                "selected_different_size",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("false"),
            )
        )
        b.add_column(
            sa.Column(
                "feedback_basis",
                sa.String(length=32),
                nullable=False,
                server_default="RECOMMENDATION_ONLY",
            )
        )
        b.add_column(sa.Column("comment", sa.Text(), nullable=True))
        b.add_column(
            sa.Column(
                "review_status",
                sa.String(length=32),
                nullable=False,
                server_default="UNVERIFIED",
            )
        )
        b.add_column(sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True))
        b.add_column(sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
        b.create_unique_constraint(
            "uq_fit_feedback_rec_user", ["recommendation_id", "user_id"]
        )

    op.create_index("ix_fit_feedback_recommendation", "fit_feedback", ["recommendation_id"])

    # 3. Create fit_recommendation_evidence
    op.create_table(
        "fit_recommendation_evidence",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "recommendation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("fit_recommendations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("source_type", sa.String(length=64), nullable=False),
        sa.Column("source_id", sa.String(length=128), nullable=False),
        sa.Column("source_revision", sa.String(length=64), nullable=False),
        sa.Column("measurement_basis", sa.String(length=16), nullable=True),
        sa.Column("evidence_status", sa.String(length=32), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_fit_rec_evidence_rec", "fit_recommendation_evidence", ["recommendation_id"]
    )
    op.create_index(
        "ix_fit_rec_evidence_source",
        "fit_recommendation_evidence",
        ["source_type", "source_id"],
    )

    # 4. Create fit_recommendation_candidates
    op.create_table(
        "fit_recommendation_candidates",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "recommendation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("fit_recommendations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("variant_id", sa.String(length=128), nullable=False),
        sa.Column("merchant_size_label", sa.String(length=64), nullable=False),
        sa.Column("is_available", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("matched", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("mismatched_fields_json", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("rank_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_fit_rec_candidates_rec", "fit_recommendation_candidates", ["recommendation_id"]
    )

    # 5. Create fit_evaluation_cases
    op.create_table(
        "fit_evaluation_cases",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("dataset_version", sa.String(length=64), nullable=False),
        sa.Column("case_key", sa.String(length=128), nullable=False),
        sa.Column("split_name", sa.String(length=24), nullable=False),
        sa.Column("merchant_id", sa.String(length=128), nullable=False),
        sa.Column("product_id", sa.String(length=128), nullable=False),
        sa.Column("merchant_offer_id", sa.String(length=128), nullable=False),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("variant_id", sa.String(length=128), nullable=True),
        sa.Column("size_chart_revision", sa.Integer(), nullable=False),
        sa.Column("measurement_basis", sa.String(length=16), nullable=False),
        sa.Column("shopper_snapshot_json", sa.JSON(), nullable=False),
        sa.Column("expected_label", sa.String(length=40), nullable=False),
        sa.Column("expected_size", sa.String(length=64), nullable=True),
        sa.Column("acceptable_sizes_json", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("reviewer_id", sa.String(length=128), nullable=False),
        sa.Column("labelled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("evidence_reference", sa.String(length=512), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("dataset_version", "case_key", name="uq_fit_eval_case_version_key"),
    )
    op.create_index(
        "ix_fit_eval_cases_dataset", "fit_evaluation_cases", ["dataset_version", "split_name"]
    )
    op.create_index("ix_fit_eval_cases_merchant", "fit_evaluation_cases", ["merchant_id"])

    # 6. Create fit_evaluation_runs
    op.create_table(
        "fit_evaluation_runs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("dataset_version", sa.String(length=64), nullable=False),
        sa.Column("fit_algorithm_version", sa.String(length=32), nullable=False),
        sa.Column("category_policy_version", sa.String(length=32), nullable=False),
        sa.Column("total_cases", sa.Integer(), nullable=False),
        sa.Column("recommended_count", sa.Integer(), nullable=False),
        sa.Column("abstention_count", sa.Integer(), nullable=False),
        sa.Column("exact_size_accuracy", sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column("acceptable_size_accuracy", sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column("coverage", sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column("abstention_rate", sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column("false_recommendation_rate", sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column("metrics_json", sa.JSON(), nullable=False),
        sa.Column("gate_passed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_fit_eval_runs_dataset", "fit_evaluation_runs", ["dataset_version"])
    op.create_index("ix_fit_eval_runs_created", "fit_evaluation_runs", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_fit_eval_runs_created", table_name="fit_evaluation_runs")
    op.drop_index("ix_fit_eval_runs_dataset", table_name="fit_evaluation_runs")
    op.drop_table("fit_evaluation_runs")

    op.drop_index("ix_fit_eval_cases_merchant", table_name="fit_evaluation_cases")
    op.drop_index("ix_fit_eval_cases_dataset", table_name="fit_evaluation_cases")
    op.drop_table("fit_evaluation_cases")

    op.drop_index("ix_fit_rec_candidates_rec", table_name="fit_recommendation_candidates")
    op.drop_table("fit_recommendation_candidates")

    op.drop_index("ix_fit_rec_evidence_source", table_name="fit_recommendation_evidence")
    op.drop_index("ix_fit_rec_evidence_rec", table_name="fit_recommendation_evidence")
    op.drop_table("fit_recommendation_evidence")

    op.drop_index("ix_fit_feedback_recommendation", table_name="fit_feedback")
    with op.batch_alter_table("fit_feedback") as b:
        b.drop_constraint("uq_fit_feedback_rec_user", type_="unique")
        b.drop_column("deleted_at")
        b.drop_column("reviewed_at")
        b.drop_column("review_status")
        b.drop_column("comment")
        b.drop_column("feedback_basis")
        b.drop_column("selected_different_size")
        b.drop_column("kept_item")
        b.drop_column("tried_on")
        b.drop_column("purchase_status")
        b.drop_column("reason")
        b.drop_column("size_chart_revision")
        b.drop_column("size_chart_id")
        b.drop_column("merchant_offer_id")
        b.drop_column("merchant_id")
        b.drop_column("recommendation_id")
        b.alter_column("brand_id", existing_type=sa.UUID(), nullable=False)

    op.drop_index("ix_fit_recommendations_valid", table_name="fit_recommendations")
    op.drop_index("ix_fit_recommendations_chart", table_name="fit_recommendations")
    op.drop_index("ix_fit_recommendations_offer", table_name="fit_recommendations")
    with op.batch_alter_table("fit_recommendations") as b:
        b.alter_column(
            "recommended_size",
            existing_type=sa.String(length=64),
            type_=sa.String(length=32),
            existing_nullable=True,
        )
        b.alter_column(
            "outcome",
            existing_type=sa.String(length=40),
            type_=sa.String(length=32),
            existing_nullable=False,
        )
        b.drop_column("expires_at")
        b.drop_column("invalidated_at")
        b.drop_column("invalidation_reason")
        b.drop_column("internal_confidence_score")
        b.drop_column("reason_codes_json")
        b.drop_column("recommendation_status")
        b.drop_column("source_permission_revision")
        b.drop_column("fit_preference_revision")
        b.drop_column("fit_algorithm_version")
        b.drop_column("category_policy_version")
        b.drop_column("shopper_measurement_revision")
        b.drop_column("size_chart_revision")
        b.drop_column("size_chart_id")
        b.drop_column("variant_id")
        b.drop_column("merchant_product_id")
        b.drop_column("merchant_id")
