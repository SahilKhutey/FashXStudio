"""Add issue_tags column to tryon_feedback

Revision ID: 0032_tryon_feedback_issue_tags
Revises: 0031_tryon_jobs_locked_by
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0032_tryon_feedback_issue_tags"
down_revision: str | None = "0031_tryon_jobs_locked_by"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("tryon_feedback") as b:
        b.add_column(
            sa.Column(
                "issue_tags",
                sa.JSON(),
                nullable=False,
                server_default=sa.text("'[]'"),
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("tryon_feedback") as b:
        b.drop_column("issue_tags")
