"""Add catalog evaluation runs and link health check records

Revision ID: 0044_add_catalog_evaluation_runs
Revises: 0043_add_merchant_catalog_operations
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0044_add_catalog_evaluation_runs"
down_revision: str | None = "0043_add_merchant_catalog_operations"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Create catalog_evaluation_runs
    op.create_table(
        "catalog_evaluation_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "configuration_version", sa.String(length=32), server_default="1.0", nullable=False
        ),
        sa.Column("status", sa.String(length=32), server_default="COMPLETED", nullable=False),
        sa.Column("all_passed", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("metrics_summary", sa.JSON(), server_default="{}", nullable=False),
        sa.Column("detailed_report", sa.JSON(), server_default="{}", nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column(
            "started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_catalog_eval_runs_created",
        "catalog_evaluation_runs",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        "ix_catalog_eval_runs_status",
        "catalog_evaluation_runs",
        ["status"],
        unique=False,
    )

    # 2. Create catalog_link_health_checks
    op.create_table(
        "catalog_link_health_checks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("offer_id", sa.Uuid(), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), server_default="UNVERIFIED", nullable=False),
        sa.Column("http_status", sa.Integer(), nullable=True),
        sa.Column(
            "checked_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("response_time_ms", sa.Integer(), nullable=True),
        sa.Column("redirect_url", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["offer_id"], ["merchant_offers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_link_health_offer",
        "catalog_link_health_checks",
        ["offer_id"],
        unique=False,
    )
    op.create_index(
        "ix_link_health_status",
        "catalog_link_health_checks",
        ["status"],
        unique=False,
    )
    op.create_index(
        "ix_link_health_checked",
        "catalog_link_health_checks",
        ["checked_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_link_health_checked", table_name="catalog_link_health_checks")
    op.drop_index("ix_link_health_status", table_name="catalog_link_health_checks")
    op.drop_index("ix_link_health_offer", table_name="catalog_link_health_checks")
    op.drop_table("catalog_link_health_checks")

    op.drop_index("ix_catalog_eval_runs_status", table_name="catalog_evaluation_runs")
    op.drop_index("ix_catalog_eval_runs_created", table_name="catalog_evaluation_runs")
    op.drop_table("catalog_evaluation_runs")
