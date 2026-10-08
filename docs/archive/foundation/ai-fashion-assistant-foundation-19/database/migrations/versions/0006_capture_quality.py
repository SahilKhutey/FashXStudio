"""add structured capture quality and pose metadata"""

from collections.abc import Sequence
from alembic import op
import sqlalchemy as sa

revision: str = "0006_capture_quality"
down_revision: str | Sequence[str] | None = "0005_profile_photo_validation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("user_photos", sa.Column("quality_score", sa.Float(), nullable=True))
    op.add_column("user_photos", sa.Column("pose_score", sa.Float(), nullable=True))
    op.add_column("user_photos", sa.Column("framing_score", sa.Float(), nullable=True))
    op.add_column("user_photos", sa.Column("landmark_confidence", sa.Float(), nullable=True))
    op.add_column("user_photos", sa.Column("ready_for_tryon", sa.Boolean(), nullable=True))
    op.add_column("user_photos", sa.Column("quality_reasons", sa.JSON(), nullable=True))
    op.add_column("user_photos", sa.Column("pose_provider", sa.String(length=64), nullable=True))
    op.add_column("user_photos", sa.Column("pose_provider_version", sa.String(length=64), nullable=True))


def downgrade() -> None:
    op.drop_column("user_photos", "pose_provider_version")
    op.drop_column("user_photos", "pose_provider")
    op.drop_column("user_photos", "quality_reasons")
    op.drop_column("user_photos", "ready_for_tryon")
    op.drop_column("user_photos", "landmark_confidence")
    op.drop_column("user_photos", "framing_score")
    op.drop_column("user_photos", "pose_score")
    op.drop_column("user_photos", "quality_score")
