"""foundation: extensions and migration baseline"""

from collections.abc import Sequence

from alembic import op

revision: str = "0001_foundation"
down_revision: str | Sequence[str] | None = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("ALTER TABLE alembic_version ALTER COLUMN version_num TYPE VARCHAR(64)")


def downgrade() -> None:
    op.execute("DROP EXTENSION IF EXISTS vector")
