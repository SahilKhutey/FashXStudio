"""try-on feedback uniqueness and instrumentation"""

from alembic import op

revision = "0011_tryon_feedback_instrumentation"
down_revision = "0010_tryon_result_quality"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_unique_constraint(
        "uq_tryon_feedback_user_job",
        "tryon_feedback",
        ["user_id", "tryon_job_id"],
    )

def downgrade() -> None:
    op.drop_constraint("uq_tryon_feedback_user_job", "tryon_feedback", type_="unique")
