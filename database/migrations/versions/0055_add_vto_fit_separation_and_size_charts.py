"""Add VTO fit separation, fit recommendations, size charts, and feedback reviews (Phase 07.8)

Revision ID: 0055_add_vto_fit_separation_and_size_charts
Revises: 0054_add_tryon_quality_evaluation
Create Date: 2026-11-25 09:30:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0055_add_vto_fit_separation_and_size_charts"
down_revision: str | None = "0054_add_tryon_quality_evaluation"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Update tryon_feedback with Phase 07.8 fields
    with op.batch_alter_table("tryon_feedback") as b:
        b.add_column(sa.Column("reason_code", sa.String(length=64), nullable=True))
        b.add_column(sa.Column("details", sa.Text(), nullable=True))
        b.add_column(
            sa.Column(
                "include_in_quality_review",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("false"),
            )
        )
        b.add_column(
            sa.Column(
                "review_status",
                sa.String(length=32),
                nullable=False,
                server_default="RECEIVED",
            )
        )
        b.alter_column("visual_accuracy", existing_type=sa.String(length=32), nullable=True)

    # 2. fit_recommendations table
    op.create_table(
        "fit_recommendations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "product_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("canonical_garments.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "merchant_offer_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("merchant_offers.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("outcome", sa.String(length=32), nullable=False),
        sa.Column("recommended_size", sa.String(length=32), nullable=True),
        sa.Column("alternative_sizes", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("explanation_code", sa.String(length=64), nullable=False),
        sa.Column("evidence_json", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("fit_model_version", sa.String(length=64), nullable=False),
        sa.Column(
            "is_valid",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_fit_recommendations_user", "fit_recommendations", ["user_id"])
    op.create_index("ix_fit_recommendations_product", "fit_recommendations", ["product_id"])
    op.create_index("ix_fit_recommendations_created", "fit_recommendations", ["created_at"])

    # 3. tryon_feedback_reviews table
    op.create_table(
        "tryon_feedback_reviews",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "feedback_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tryon_feedback.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("reviewer_id", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("root_cause", sa.String(length=64), nullable=True),
        sa.Column("severity", sa.String(length=32), nullable=True),
        sa.Column("resolution_notes", sa.Text(), nullable=True),
        sa.Column(
            "linked_evaluation_item_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tryon_evaluation_items.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "category_action_required",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_tryon_feedback_reviews_feedback", "tryon_feedback_reviews", ["feedback_id"])
    op.create_index("ix_tryon_feedback_reviews_reviewer", "tryon_feedback_reviews", ["reviewer_id"])
    op.create_index("ix_tryon_feedback_reviews_status", "tryon_feedback_reviews", ["status"])

    # 4. merchant_verified_size_charts table
    op.create_table(
        "merchant_verified_size_charts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "merchant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("merchants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "canonical_garment_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("canonical_garments.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("merchant_product_id", sa.String(length=255), nullable=False),
        sa.Column("merchant_name", sa.String(length=255), nullable=False),
        sa.Column("basis", sa.String(length=16), nullable=False),
        sa.Column("unit", sa.String(length=8), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="VERIFIED"),
        sa.Column("source_reference", sa.String(length=512), nullable=False),
        sa.Column("source_revision", sa.String(length=64), nullable=False),
        sa.Column("rows_json", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("chart_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "last_verified_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
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
    )
    op.create_index("ix_merchant_size_charts_merchant", "merchant_verified_size_charts", ["merchant_id"])
    op.create_index("ix_merchant_size_charts_garment", "merchant_verified_size_charts", ["canonical_garment_id"])
    op.create_index("ix_merchant_size_charts_product", "merchant_verified_size_charts", ["merchant_product_id"])
    op.create_index("ix_merchant_size_charts_status", "merchant_verified_size_charts", ["status"])


def downgrade() -> None:
    # 4. Drop merchant_verified_size_charts
    op.drop_index("ix_merchant_size_charts_status", table_name="merchant_verified_size_charts")
    op.drop_index("ix_merchant_size_charts_product", table_name="merchant_verified_size_charts")
    op.drop_index("ix_merchant_size_charts_garment", table_name="merchant_verified_size_charts")
    op.drop_index("ix_merchant_size_charts_merchant", table_name="merchant_verified_size_charts")
    op.drop_table("merchant_verified_size_charts")

    # 3. Drop tryon_feedback_reviews
    op.drop_index("ix_tryon_feedback_reviews_status", table_name="tryon_feedback_reviews")
    op.drop_index("ix_tryon_feedback_reviews_reviewer", table_name="tryon_feedback_reviews")
    op.drop_index("ix_tryon_feedback_reviews_feedback", table_name="tryon_feedback_reviews")
    op.drop_table("tryon_feedback_reviews")

    # 2. Drop fit_recommendations
    op.drop_index("ix_fit_recommendations_created", table_name="fit_recommendations")
    op.drop_index("ix_fit_recommendations_product", table_name="fit_recommendations")
    op.drop_index("ix_fit_recommendations_user", table_name="fit_recommendations")
    op.drop_table("fit_recommendations")

    # 1. Revert tryon_feedback columns
    with op.batch_alter_table("tryon_feedback") as b:
        b.alter_column("visual_accuracy", existing_type=sa.String(length=32), nullable=False)
        b.drop_column("review_status")
        b.drop_column("include_in_quality_review")
        b.drop_column("details")
        b.drop_column("reason_code")
