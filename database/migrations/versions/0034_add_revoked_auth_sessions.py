"""Add revoked_auth_sessions table

Revision ID: 0034_add_revoked_auth_sessions
Revises: 0033_add_worker_dead_letters
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0034_add_revoked_auth_sessions"
down_revision: str | None = "0033_add_worker_dead_letters"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "revoked_auth_sessions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("identity_provider", sa.String(length=32), nullable=False),
        sa.Column("subject", sa.String(length=255), nullable=False),
        sa.Column("session_id", sa.String(length=255), nullable=False),
        sa.Column(
            "revoked_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "identity_provider",
            "session_id",
            name="uq_revoked_auth_sessions_provider_session",
        ),
    )
    op.create_index(
        "ix_revoked_auth_sessions_subject",
        "revoked_auth_sessions",
        ["subject"],
    )
    op.create_index(
        "ix_revoked_auth_sessions_session_id",
        "revoked_auth_sessions",
        ["session_id"],
    )
    op.create_index(
        "ix_revoked_auth_sessions_expires_at",
        "revoked_auth_sessions",
        ["expires_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_revoked_auth_sessions_expires_at",
        table_name="revoked_auth_sessions",
    )
    op.drop_index(
        "ix_revoked_auth_sessions_session_id",
        table_name="revoked_auth_sessions",
    )
    op.drop_index(
        "ix_revoked_auth_sessions_subject",
        table_name="revoked_auth_sessions",
    )
    op.drop_table("revoked_auth_sessions")
