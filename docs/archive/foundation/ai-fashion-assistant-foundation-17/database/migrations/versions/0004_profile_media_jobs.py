"""add profile photo processing jobs"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0004_profile_media_jobs"
down_revision: str | Sequence[str] | None = "0003_operations_and_vector_upgrade"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "profile_photo_jobs",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("photo_id", sa.UUID(), sa.ForeignKey("user_photos.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(length=32), server_default="queued", nullable=False),
        sa.Column("failure_reason", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_profile_photo_jobs_photo_id", "profile_photo_jobs", ["photo_id"])
    op.create_index("ix_profile_photo_jobs_user_id", "profile_photo_jobs", ["user_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_profile_photo_jobs_user_id", table_name="profile_photo_jobs")
    op.drop_index("ix_profile_photo_jobs_photo_id", table_name="profile_photo_jobs")
    op.drop_table("profile_photo_jobs")
