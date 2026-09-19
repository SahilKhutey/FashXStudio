"""add profile photo validation metadata and worker state"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0005_profile_photo_validation"
down_revision: str | Sequence[str] | None = "0004_profile_media_jobs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("user_photos", sa.Column("content_sha256", sa.String(length=64), nullable=True))
    op.add_column("user_photos", sa.Column("width", sa.Integer(), nullable=True))
    op.add_column("user_photos", sa.Column("height", sa.Integer(), nullable=True))
    op.add_column("user_photos", sa.Column("image_format", sa.String(length=16), nullable=True))
    op.add_column("user_photos", sa.Column("file_size_bytes", sa.Integer(), nullable=True))
    op.add_column("user_photos", sa.Column("has_person", sa.Boolean(), nullable=True))
    op.add_column("user_photos", sa.Column("has_face", sa.Boolean(), nullable=True))
    op.create_index("ix_user_photos_content_sha256", "user_photos", ["content_sha256"])

    op.add_column("profile_photo_jobs", sa.Column("attempt_count", sa.Integer(), server_default="0", nullable=False))
    op.add_column("profile_photo_jobs", sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("profile_photo_jobs", sa.Column("last_error", sa.Text(), nullable=True))
    op.create_index("ix_profile_photo_jobs_status", "profile_photo_jobs", ["status", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_profile_photo_jobs_status", table_name="profile_photo_jobs")
    op.drop_column("profile_photo_jobs", "last_error")
    op.drop_column("profile_photo_jobs", "locked_at")
    op.drop_column("profile_photo_jobs", "attempt_count")
    op.drop_index("ix_user_photos_content_sha256", table_name="user_photos")
    op.drop_column("user_photos", "has_face")
    op.drop_column("user_photos", "has_person")
    op.drop_column("user_photos", "file_size_bytes")
    op.drop_column("user_photos", "image_format")
    op.drop_column("user_photos", "height")
    op.drop_column("user_photos", "width")
    op.drop_column("user_photos", "content_sha256")
