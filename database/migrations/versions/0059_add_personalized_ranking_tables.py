"""Add Phase 08.4 personalized product ranking tables

Revision ID: 0059_add_personalized_ranking_tables
Revises: 0058_add_fit_recommendation_snapshot_feedback_eval
Create Date: 2026-11-27 09:25:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0059_add_personalized_ranking_tables"
down_revision: str | None = "0058_add_fit_recommendation_snapshot_feedback_eval"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Create product_feedback table
    op.create_table(
        "product_feedback",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("product_id", sa.String(length=128), nullable=False),
        sa.Column("feedback_type", sa.String(length=30), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False, server_default="api"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint(
            "user_id",
            "product_id",
            "feedback_type",
            name="uq_product_feedback_user_product_type",
        ),
    )
    op.create_index(
        "ix_product_feedback_user_created",
        "product_feedback",
        ["user_id", "created_at"],
    )
    op.create_index(
        "ix_product_feedback_product_created",
        "product_feedback",
        ["product_id", "created_at"],
    )

    # 2. Create shopper_ranking_preferences table
    op.create_table(
        "shopper_ranking_preferences",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("style_preferences_json", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("preferred_colors_json", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("disliked_colors_json", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("preferred_categories_json", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("budget_min", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("budget_max", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="INR"),
        sa.Column("revision", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("user_id", name="uq_shopper_ranking_preferences_user"),
    )
    op.create_index(
        "ix_shopper_ranking_preferences_user",
        "shopper_ranking_preferences",
        ["user_id"],
    )

    # 3. Create ranking_events table
    op.create_table(
        "ranking_events",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("request_id", sa.String(length=64), nullable=False),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("ranking_version", sa.String(length=32), nullable=False),
        sa.Column("config_version", sa.String(length=32), nullable=False),
        sa.Column("taxonomy_version", sa.String(length=32), nullable=False),
        sa.Column("experiment_group", sa.String(length=32), nullable=True),
        sa.Column("candidate_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("eligible_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("returned_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("results_snapshot_json", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_ranking_events_version_created",
        "ranking_events",
        ["ranking_version", "created_at"],
    )
    op.create_index(
        "ix_ranking_events_user_created",
        "ranking_events",
        ["user_id", "created_at"],
    )

    # 4. Create ranking_evaluation_runs table
    op.create_table(
        "ranking_evaluation_runs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("dataset_version", sa.String(length=64), nullable=False),
        sa.Column("baseline_version", sa.String(length=32), nullable=False),
        sa.Column("personalized_version", sa.String(length=32), nullable=False),
        sa.Column("metrics_json", sa.JSON(), nullable=False),
        sa.Column("all_gates_passed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_ranking_eval_runs_dataset",
        "ranking_evaluation_runs",
        ["dataset_version"],
    )
    op.create_index(
        "ix_ranking_eval_runs_created",
        "ranking_evaluation_runs",
        ["created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_ranking_eval_runs_created", table_name="ranking_evaluation_runs")
    op.drop_index("ix_ranking_eval_runs_dataset", table_name="ranking_evaluation_runs")
    op.drop_table("ranking_evaluation_runs")

    op.drop_index("ix_ranking_events_user_created", table_name="ranking_events")
    op.drop_index("ix_ranking_events_version_created", table_name="ranking_events")
    op.drop_table("ranking_events")

    op.drop_index("ix_shopper_ranking_preferences_user", table_name="shopper_ranking_preferences")
    op.drop_table("shopper_ranking_preferences")

    op.drop_index("ix_product_feedback_product_created", table_name="product_feedback")
    op.drop_index("ix_product_feedback_user_created", table_name="product_feedback")
    op.drop_table("product_feedback")
