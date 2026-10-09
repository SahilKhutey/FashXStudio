"""outbox messages table

Revision ID: 0015_outbox_messages
Revises: 0014_auth_identities
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0015_outbox_messages"
down_revision: str | None = "0014_auth_identities"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "outbox_messages",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("topic", sa.String(255), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "next_attempt_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
    )
    op.create_index(
        "ix_outbox_messages_next_attempt_at", "outbox_messages", ["next_attempt_at"]
    )


def downgrade() -> None:
    op.drop_index(
        "ix_outbox_messages_next_attempt_at", table_name="outbox_messages"
    )
    op.drop_table("outbox_messages")
