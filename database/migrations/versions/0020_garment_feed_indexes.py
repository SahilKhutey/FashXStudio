"""garment feed search indexes and denormalized feed filter columns

Revision ID: 0020_garment_feed_indexes
Revises: 0019_feed_logging
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0020_garment_feed_indexes"
down_revision: str | None = "0019_feed_logging"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Add denormalized feed query columns to canonical_garments if not present
    op.add_column(
        "canonical_garments",
        sa.Column("gender", sa.String(32), nullable=False, server_default="unisex"),
    )
    op.add_column(
        "canonical_garments",
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.add_column(
        "canonical_garments",
        sa.Column("in_stock", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.add_column(
        "canonical_garments",
        sa.Column("price_minor", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "canonical_garments",
        sa.Column(
            "price_updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.add_column(
        "canonical_garments",
        sa.Column(
            "sizes_in_stock",
            postgresql.ARRAY(sa.String(32)),
            nullable=False,
            server_default=sa.text("ARRAY['S','M','L']::character varying(32)[]"),
        ),
    )

    # 2. GIN Index on sizes_in_stock for fast array intersection queries (@>)
    op.create_index(
        "ix_garments_sizes_in_stock_gin",
        "canonical_garments",
        ["sizes_in_stock"],
        postgresql_using="gin",
    )

    # 3. Composite index on feed hard-filter columns
    op.create_index(
        "ix_garments_feed",
        "canonical_garments",
        ["category", "gender", "active", "in_stock"],
    )

    # 4. Index on price for budget bounds
    op.create_index(
        "ix_garments_price",
        "canonical_garments",
        ["price_minor"],
    )


def downgrade() -> None:
    op.drop_index("ix_garments_price", table_name="canonical_garments")
    op.drop_index("ix_garments_feed", table_name="canonical_garments")
    op.drop_index("ix_garments_sizes_in_stock_gin", table_name="canonical_garments")
    op.drop_column("canonical_garments", "sizes_in_stock")
    op.drop_column("canonical_garments", "price_updated_at")
    op.drop_column("canonical_garments", "price_minor")
    op.drop_column("canonical_garments", "in_stock")
    op.drop_column("canonical_garments", "active")
    op.drop_column("canonical_garments", "gender")
