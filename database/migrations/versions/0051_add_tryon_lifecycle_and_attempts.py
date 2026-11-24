"""Add tryon lifecycle fields and provider attempts table (Phase 07.4)

Revision ID: 0051_add_tryon_lifecycle_and_attempts
Revises: 0050_add_tryon_input_validations
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0051_add_tryon_lifecycle_and_attempts"
down_revision: str | None = "0050_add_tryon_input_validations"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Add lifecycle columns to tryon_jobs
    op.add_column("tryon_jobs", sa.Column("request_hash", sa.String(length=64), nullable=True))
    op.add_column("tryon_jobs", sa.Column("provider_submitted_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("tryon_jobs", sa.Column("provider_completed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("tryon_jobs", sa.Column("started_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("tryon_jobs", sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("tryon_jobs", sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("tryon_jobs", sa.Column("validation_policy_version", sa.String(length=64), nullable=True))
    op.add_column("tryon_jobs", sa.Column("error_code", sa.String(length=64), nullable=True))
    op.add_column(
        "tryon_jobs",
        sa.Column("progress_stage", sa.String(length=64), server_default="waiting_for_worker", nullable=True),
    )
    op.add_column("tryon_jobs", sa.Column("lock_expires_at", sa.DateTime(timezone=True), nullable=True))

    op.create_index(
        "ix_tryon_jobs_status_created",
        "tryon_jobs",
        ["status", "created_at"],
    )
    op.create_index(
        "ix_tryon_jobs_prov_job",
        "tryon_jobs",
        ["provider", "provider_job_id"],
    )

    # 2. Add provenance columns to tryon_artifacts
    op.add_column("tryon_artifacts", sa.Column("provider", sa.String(length=64), nullable=True))
    op.add_column("tryon_artifacts", sa.Column("provider_model_version", sa.String(length=64), nullable=True))
    op.add_column("tryon_artifacts", sa.Column("source_image_sha256", sa.String(length=64), nullable=True))
    op.add_column("tryon_artifacts", sa.Column("garment_image_sha256", sa.String(length=64), nullable=True))
    op.add_column("tryon_artifacts", sa.Column("output_sha256", sa.String(length=64), nullable=True))
    op.add_column("tryon_artifacts", sa.Column("processing_latency_ms", sa.Integer(), nullable=True))

    # 3. Create tryon_provider_attempts table
    op.create_table(
        "tryon_provider_attempts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "job_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tryon_jobs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("model_version", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("provider_job_id", sa.String(length=255), nullable=True),
        sa.Column("request_hash", sa.String(length=64), nullable=False),
        sa.Column("provider_error_code", sa.String(length=128), nullable=True),
        sa.Column("safe_error_detail", sa.Text(), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("job_id", "attempt_number", name="uq_tryon_provider_attempt_job_num"),
    )
    op.create_index(
        "ix_tryon_provider_attempt_job",
        "tryon_provider_attempts",
        ["job_id"],
    )
    op.create_index(
        "ix_tryon_provider_attempt_status",
        "tryon_provider_attempts",
        ["status", "created_at"],
    )
    op.create_index(
        "ix_tryon_provider_attempt_prov_job",
        "tryon_provider_attempts",
        ["provider", "provider_job_id"],
    )


def downgrade() -> None:
    # 3. Drop tryon_provider_attempts table
    op.drop_index("ix_tryon_provider_attempt_prov_job", table_name="tryon_provider_attempts")
    op.drop_index("ix_tryon_provider_attempt_status", table_name="tryon_provider_attempts")
    op.drop_index("ix_tryon_provider_attempt_job", table_name="tryon_provider_attempts")
    op.drop_table("tryon_provider_attempts")

    # 2. Drop columns from tryon_artifacts
    op.drop_column("tryon_artifacts", "processing_latency_ms")
    op.drop_column("tryon_artifacts", "output_sha256")
    op.drop_column("tryon_artifacts", "garment_image_sha256")
    op.drop_column("tryon_artifacts", "source_image_sha256")
    op.drop_column("tryon_artifacts", "provider_model_version")
    op.drop_column("tryon_artifacts", "provider")

    # 1. Drop columns and indexes from tryon_jobs
    op.drop_index("ix_tryon_jobs_prov_job", table_name="tryon_jobs")
    op.drop_index("ix_tryon_jobs_status_created", table_name="tryon_jobs")
    op.drop_column("tryon_jobs", "lock_expires_at")
    op.drop_column("tryon_jobs", "progress_stage")
    op.drop_column("tryon_jobs", "error_code")
    op.drop_column("tryon_jobs", "validation_policy_version")
    op.drop_column("tryon_jobs", "expires_at")
    op.drop_column("tryon_jobs", "updated_at")
    op.drop_column("tryon_jobs", "started_at")
    op.drop_column("tryon_jobs", "provider_completed_at")
    op.drop_column("tryon_jobs", "provider_submitted_at")
    op.drop_column("tryon_jobs", "request_hash")
