"""Add unique constraint on wardrobe_items (user_id, garment_id)

Revision ID: 0030_wardrobe_user_garment_unique
Revises: 0029_consent_events
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0030_wardrobe_user_garment_unique"
down_revision: str | None = "0029_consent_events"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("wardrobe_items") as b:
        b.create_unique_constraint("uq_wardrobe_user_garment", ["user_id", "garment_id"])


def downgrade() -> None:
    with op.batch_alter_table("wardrobe_items") as b:
        b.drop_constraint("uq_wardrobe_user_garment", type_="unique")
