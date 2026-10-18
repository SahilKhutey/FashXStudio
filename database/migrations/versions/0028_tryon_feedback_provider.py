"""Add provider to tryon_feedback

Revision ID: 0028_tryon_feedback_provider
Revises: 0027_embedding_model
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0028_tryon_feedback_provider"
down_revision: str | None = "0027_embedding_model"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("tryon_feedback") as b:
        b.add_column(sa.Column("provider", sa.String(length=64), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("tryon_feedback") as b:
        b.drop_column("provider")
