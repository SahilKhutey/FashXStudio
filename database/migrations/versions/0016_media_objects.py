"""media objects table

Revision ID: 0016_media_objects
Revises: 0015_outbox_messages
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0016_media_objects"
down_revision: str | None = "0015_outbox_messages"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "media_objects",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("kind", sa.String(32), nullable=False),
        sa.Column("object_key", sa.Text(), nullable=False, unique=True),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("content_type", sa.String(64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "kind in ('reference_photo', 'tryon_result', 'garment_render')",
            name="ck_media_kind",
        ),
    )
    op.create_index("ix_media_user_kind", "media_objects", ["user_id", "kind"])


def downgrade() -> None:
    op.drop_index("ix_media_user_kind", table_name="media_objects")
    op.drop_table("media_objects")
