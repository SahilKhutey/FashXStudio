"""auth identities table

Revision ID: 0014_auth_identities
Revises: 0013_onboarding_profiles
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0014_auth_identities"
down_revision: str | None = "0013_onboarding_profiles"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "auth_identities",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("issuer", sa.String(255), nullable=False),
        sa.Column("subject", sa.String(255), nullable=False),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(32), nullable=False, server_default="user"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("disabled_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("issuer", "subject", name="uq_auth_identities_issuer_subject"),
    )
    op.create_index("ix_auth_identities_user_id", "auth_identities", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_auth_identities_user_id", table_name="auth_identities")
    op.drop_table("auth_identities")
