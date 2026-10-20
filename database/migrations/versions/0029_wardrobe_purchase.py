"""Add purchased_at to wardrobe_items

Revision ID: 0029_wardrobe_purchase
Revises: 0028_tryon_feedback_provider
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0029_wardrobe_purchase"
down_revision: str | None = "0028_tryon_feedback_provider"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("wardrobe_items") as b:
        b.add_column(sa.Column("purchased_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("wardrobe_items") as b:
        b.drop_column("purchased_at")
