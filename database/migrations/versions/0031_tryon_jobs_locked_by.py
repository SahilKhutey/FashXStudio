"""Add locked_by column to tryon_jobs

Revision ID: 0031_tryon_jobs_locked_by
Revises: 0030_wardrobe_user_garment_unique
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0031_tryon_jobs_locked_by"
down_revision: str | None = "0030_wardrobe_user_garment_unique"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("tryon_jobs") as b:
        b.add_column(sa.Column("locked_by", sa.String(128), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("tryon_jobs") as b:
        b.drop_column("locked_by")
