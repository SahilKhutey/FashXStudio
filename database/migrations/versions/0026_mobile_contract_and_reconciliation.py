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


def _fk_name(bind, table: str, ref_table: str, column: str) -> str | None:
    try:
        for fk in sa.inspect(bind).get_foreign_keys(table):
            if fk["referred_table"] == ref_table and fk["constrained_columns"] == [column]:
                return fk["name"]
    except Exception:
        pass
    return None


def upgrade() -> None:
    # 1. Update consent_records with mobile consent columns (fail-closed, adults only, check constraint)
    with op.batch_alter_table("consent_records") as b:
        b.add_column(sa.Column("consent_version", sa.String(length=16), nullable=False, server_default="2026.1"))
        b.add_column(sa.Column("is_18_or_older", sa.Boolean(), nullable=True))
        b.add_column(sa.Column("consented_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()))
        b.create_check_constraint(
            "ck_consent_granted_requires_adult",
            "granted IS NOT TRUE OR is_18_or_older IS TRUE",
        )
        b.create_index("ix_consent_records_user_policy", ["user_id", "consent_version"])

    # 2. Create style_quiz_picks table with indexes on user_id and garment_id
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
    op.create_index("ix_style_quiz_picks_garment_id", "style_quiz_picks", ["garment_id"])

    # 3. Canonical garments: add tryon_supported failing closed (default false)
    op.add_column(
        "canonical_garments",
        sa.Column("tryon_supported", sa.Boolean(), nullable=False, server_default=sa.false()),
    )

    # 4. Enforce ON DELETE CASCADE on tryon_jobs.profile_photo_id -> user_photos.id
    bind = op.get_bind()
    old = _fk_name(bind, "tryon_jobs", "user_photos", "profile_photo_id")
    with op.batch_alter_table("tryon_jobs") as b:
        if old:
            b.drop_constraint(old, type_="foreignkey")
        b.create_foreign_key(
            "fk_tryon_jobs_profile_photo_id_user_photos",
            "user_photos",
            ["profile_photo_id"],
            ["id"],
            ondelete="CASCADE",
        )


def downgrade() -> None:
    with op.batch_alter_table("tryon_jobs") as b:
        b.drop_constraint("fk_tryon_jobs_profile_photo_id_user_photos", type_="foreignkey")
        b.create_foreign_key(
            "tryon_jobs_profile_photo_id_fkey",
            "user_photos",
            ["profile_photo_id"],
            ["id"],
            ondelete="RESTRICT",
        )
    op.drop_column("canonical_garments", "tryon_supported")
    op.drop_index("ix_style_quiz_picks_garment_id", table_name="style_quiz_picks")
    op.drop_index("ix_style_quiz_picks_user_id", table_name="style_quiz_picks")
    op.drop_table("style_quiz_picks")
    with op.batch_alter_table("consent_records") as b:
        b.drop_constraint("ck_consent_granted_requires_adult", type_="check")
        b.drop_index("ix_consent_records_user_policy")
        b.drop_column("consented_at")
        b.drop_column("is_18_or_older")
        b.drop_column("consent_version")
