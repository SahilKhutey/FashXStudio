"""feature flags and kill switches

Revision ID: 0022_feature_flags
Revises: 0021_erasure_tombstones
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0022_feature_flags"
down_revision: str | None = "0021_erasure_tombstones"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    flags_table = op.create_table(
        "feature_flags",
        sa.Column("name", sa.String(64), primary_key=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("updated_by", sa.String(128), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
    )

    # Seed default flags
    op.bulk_insert(
        flags_table,
        [
            {
                "name": "tryon_enabled",
                "enabled": True,
                "description": "Virtual try-on processing and job submission kill switch",
                "updated_by": "system_bootstrap",
                "reason": "Default active state",
            },
            {
                "name": "maintenance_mode",
                "enabled": False,
                "description": "System-wide maintenance mode blocking non-admin traffic with 503",
                "updated_by": "system_bootstrap",
                "reason": "Default inactive state",
            },
            {
                "name": "ingest_enabled",
                "enabled": True,
                "description": "Catalog ingestion polling worker kill switch",
                "updated_by": "system_bootstrap",
                "reason": "Default active state",
            },
            {
                "name": "signups_open",
                "enabled": True,
                "description": "New pilot user onboarding and account creation gate",
                "updated_by": "system_bootstrap",
                "reason": "Default active state",
            },
        ],
    )


def downgrade() -> None:
    op.drop_table("feature_flags")
