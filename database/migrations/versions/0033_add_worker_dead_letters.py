"""Add worker_dead_letters table

Revision ID: 0033_add_worker_dead_letters
Revises: 0032_tryon_feedback_issue_tags
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0033_add_worker_dead_letters"
down_revision: str | None = "0032_tryon_feedback_issue_tags"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "worker_dead_letters",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("task_id", sa.String(length=255), nullable=False),
        sa.Column("task_name", sa.String(length=255), nullable=False),
        sa.Column("queue_name", sa.String(length=100), nullable=False),
        sa.Column("error_type", sa.String(length=255), nullable=False),
        sa.Column("error_message", sa.String(length=1000), nullable=False),
        sa.Column(
            "safe_payload",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'{}'"),
        ),
        sa.Column(
            "status",
            sa.String(length=30),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_worker_dead_letters_task_id",
        "worker_dead_letters",
        ["task_id"],
        unique=True,
    )
    op.create_index(
        "ix_worker_dead_letters_status",
        "worker_dead_letters",
        ["status"],
    )
    op.create_index(
        "ix_worker_dead_letters_created_at",
        "worker_dead_letters",
        ["created_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_worker_dead_letters_created_at", table_name="worker_dead_letters"
    )
    op.drop_index(
        "ix_worker_dead_letters_status", table_name="worker_dead_letters"
    )
    op.drop_index(
        "ix_worker_dead_letters_task_id", table_name="worker_dead_letters"
    )
    op.drop_table("worker_dead_letters")
