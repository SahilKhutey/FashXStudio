"""F02 mutable onboarding context

Revision ID: 0013_onboarding_profiles
Revises: 0012_analytics_indexes
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0013_onboarding_profiles"
down_revision: str | None = "0012_analytics_indexes"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "onboarding_profiles",
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("display_name", sa.String(80), nullable=False, server_default=""),
        sa.Column("avatar", sa.String(512)), sa.Column("region", sa.String(120)),
        sa.Column("status", sa.String(32), nullable=False, server_default="not_started"),
        sa.Column("step", sa.String(32), nullable=False, server_default="basic"),
        sa.Column("styles", sa.JSON(), nullable=False), sa.Column("occasions", sa.JSON(), nullable=False),
        sa.Column("fit_preferences", sa.JSON(), nullable=False),
        sa.Column("shopping_preferences", sa.JSON(), nullable=False),
        sa.Column("discovery_preferences", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("onboarding_profiles")
