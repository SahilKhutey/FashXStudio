"""feed impressions and signals logging tables

Revision ID: 0019_feed_logging
Revises: 0018_catalog_sources_and_provenance
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0019_feed_logging"
down_revision: str | None = "0018_catalog_sources_and_provenance"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "feed_impressions",
        sa.Column(
            "id",
            sa.Uuid(),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("garment_id", sa.Uuid(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("ranker_version", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index(
        "ix_impr_user_time", "feed_impressions", ["user_id", "created_at"]
    )

    op.create_table(
        "feed_signals",
        sa.Column(
            "user_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("garment_id", sa.Uuid(), nullable=False),
        sa.Column("action", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("user_id", "garment_id", "action"),
        sa.CheckConstraint(
            "action in ('like','hide','not_interested')",
            name="ck_feed_signal_action",
        ),
    )


def downgrade() -> None:
    op.drop_table("feed_signals")
    op.drop_index("ix_impr_user_time", table_name="feed_impressions")
    op.drop_table("feed_impressions")
