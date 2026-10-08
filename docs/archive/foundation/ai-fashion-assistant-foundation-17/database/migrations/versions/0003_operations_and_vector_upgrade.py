"""add idempotency records and normalize vector columns

Revision ID: 0003_operations_and_vector_upgrade
Revises: 0002_domain_foundation
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0003_operations_and_vector_upgrade"
down_revision: str | Sequence[str] | None = "0002_domain_foundation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "idempotency_records",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("key", sa.String(length=255), nullable=False),
        sa.Column("request_hash", sa.String(length=64), nullable=False),
        sa.Column("status_code", sa.Integer()),
        sa.Column("response_body", sa.JSON()),
        sa.Column("state", sa.String(length=32), server_default="in_progress", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("user_id", "key", name="uq_idempotency_user_key"),
    )
    op.create_index("ix_idempotency_records_user_id", "idempotency_records", ["user_id"])

    op.execute("ALTER TABLE user_style_profiles ALTER COLUMN embedding TYPE VECTOR(512) USING NULLIF(embedding, '')::vector")
    op.execute("ALTER TABLE garment_enrichments ALTER COLUMN embedding TYPE VECTOR(512) USING NULLIF(embedding, '')::vector")


def downgrade() -> None:
    op.execute("ALTER TABLE garment_enrichments ALTER COLUMN embedding TYPE TEXT USING embedding::text")
    op.execute("ALTER TABLE user_style_profiles ALTER COLUMN embedding TYPE TEXT USING embedding::text")
    op.drop_index("ix_idempotency_records_user_id", table_name="idempotency_records")
    op.drop_table("idempotency_records")
