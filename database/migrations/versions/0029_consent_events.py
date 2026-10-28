"""Add consent_events append-only audit table

Revision ID: 0029_consent_events
Revises: 0028_tryon_feedback_provider
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0029_consent_events"
down_revision: str | None = "0028_tryon_feedback_provider"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "consent_events",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column(
            "user_id",
            sa.UUID(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("data_type", sa.String(length=64), nullable=False),
        sa.Column("granted", sa.Boolean(), nullable=False),
        sa.Column(
            "consent_version",
            sa.String(length=16),
            nullable=False,
            server_default="2026.1",
        ),
        sa.Column("policy_url", sa.String(length=255), nullable=True),
        sa.Column(
            "decision_source",
            sa.String(length=64),
            nullable=False,
            server_default="api",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_consent_events_user_id", "consent_events", ["user_id"])
    op.create_index(
        "ix_consent_events_user_created",
        "consent_events",
        ["user_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_consent_events_user_created", table_name="consent_events")
    op.drop_index("ix_consent_events_user_id", table_name="consent_events")
    op.drop_table("consent_events")
