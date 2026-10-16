"""Mobile contract and schema reconciliation: consent, style quiz, tryon supported

Revision ID: 0026_mobile_contract_reconcile
Revises: 0025_b2b_multi_tenant
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0026_mobile_contract_reconcile"
down_revision: str | None = "0025_b2b_multi_tenant"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Update consent_records with mobile consent columns
    op.add_column("consent_records", sa.Column("policy_version", sa.String(length=16), nullable=True, server_default="2026.1"))
    op.add_column("consent_records", sa.Column("age_confirmed", sa.Boolean(), nullable=True, server_default=sa.true()))
    op.add_column("consent_records", sa.Column("parental_consent", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("consent_records", sa.Column("guardian_email", sa.String(length=255), nullable=True))
    op.add_column("consent_records", sa.Column("consented_at", sa.DateTime(timezone=True), nullable=True, server_default=sa.func.now()))
    op.create_index("ix_consent_records_user_policy", "consent_records", ["user_id", "policy_version"])

    # 2. Create style_quiz_picks table
    op.create_table(
        "style_quiz_picks",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("garment_id", sa.UUID(), sa.ForeignKey("canonical_garments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("liked", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", "garment_id", name="uq_style_quiz_picks_user_garment"),
    )
    op.create_index("ix_style_quiz_picks_user_id", "style_quiz_picks", ["user_id"])

    # 3. Canonical garments: add tryon_supported
    op.add_column(
        "canonical_garments",
        sa.Column("tryon_supported", sa.Boolean(), nullable=False, server_default=sa.true()),
    )


def downgrade() -> None:
    op.drop_column("canonical_garments", "tryon_supported")
    op.drop_index("ix_style_quiz_picks_user_id", table_name="style_quiz_picks")
    op.drop_table("style_quiz_picks")
    op.drop_index("ix_consent_records_user_policy", table_name="consent_records")
    op.drop_column("consent_records", "consented_at")
    op.drop_column("consent_records", "guardian_email")
    op.drop_column("consent_records", "parental_consent")
    op.drop_column("consent_records", "age_confirmed")
    op.drop_column("consent_records", "policy_version")
