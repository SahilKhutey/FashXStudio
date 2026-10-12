"""experiment exposures table for deterministic user-level bucketing

Revision ID: 0024_experiment_exposures
Revises: 0023_pilot_tables
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pg

revision: str = "0024_experiment_exposures"
down_revision: str | None = "0023_pilot_tables"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "experiment_exposures",
        sa.Column(
            "id",
            pg.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id",
            pg.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("experiment", sa.Text(), nullable=False),
        sa.Column("variant", sa.Text(), nullable=False),
        sa.Column(
            "first_seen_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("user_id", "experiment", name="uq_user_experiment"),
    )
    op.create_index(
        "ix_experiment_exposures_user_id",
        "experiment_exposures",
        ["user_id"],
    )
    op.create_index(
        "ix_experiment_exposures_experiment",
        "experiment_exposures",
        ["experiment"],
    )


def downgrade() -> None:
    op.drop_index("ix_experiment_exposures_experiment", table_name="experiment_exposures")
    op.drop_index("ix_experiment_exposures_user_id", table_name="experiment_exposures")
    op.drop_table("experiment_exposures")
