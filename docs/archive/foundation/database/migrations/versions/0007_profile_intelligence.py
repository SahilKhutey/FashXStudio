"""add versioned profile artifacts and skin tone results"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0007_profile_intelligence"
down_revision: str | Sequence[str] | None = "0006_capture_quality"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "skin_tone_results",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("photo_id", sa.UUID(), sa.ForeignKey("user_photos.id", ondelete="CASCADE"), nullable=False),
        sa.Column("ita_degrees", sa.Float()),
        sa.Column("tone_class", sa.String(length=64)),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("method", sa.String(length=64), nullable=False),
        sa.Column("model_version", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("photo_id", name="uq_skin_tone_results_photo"),
    )
    op.create_index("ix_skin_tone_results_user_id", "skin_tone_results", ["user_id", "created_at"])

    op.create_table(
        "profile_artifacts",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("body_snapshot", sa.JSON(), nullable=False),
        sa.Column("preferences_snapshot", sa.JSON(), nullable=False),
        sa.Column("tryon_photo_id", sa.UUID(), sa.ForeignKey("user_photos.id", ondelete="SET NULL")),
        sa.Column("skin_tone_result_id", sa.UUID(), sa.ForeignKey("skin_tone_results.id", ondelete="SET NULL")),
        sa.Column("ready_for_tryon", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", "version", name="uq_profile_artifacts_user_version"),
    )
    op.create_index("ix_profile_artifacts_user_id", "profile_artifacts", ["user_id", "version"])


def downgrade() -> None:
    op.drop_index("ix_profile_artifacts_user_id", table_name="profile_artifacts")
    op.drop_table("profile_artifacts")
    op.drop_index("ix_skin_tone_results_user_id", table_name="skin_tone_results")
    op.drop_table("skin_tone_results")
