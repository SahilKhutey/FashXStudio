"""erasure tombstones table to prevent user resurrection upon database restore

Revision ID: 0021_erasure_tombstones
Revises: 0020_garment_feed_indexes
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pg

revision: str = "0021_erasure_tombstones"
down_revision: str | None = "0020_garment_feed_indexes"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "erasure_tombstones",
        sa.Column("user_id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "erased_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )


def downgrade() -> None:
    op.drop_table("erasure_tombstones")
