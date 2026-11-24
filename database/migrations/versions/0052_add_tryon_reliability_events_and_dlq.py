"""Add tryon reliability fields, job events, and dead letters (Phase 07.5)

Revision ID: 0052_add_tryon_reliability_events_and_dlq
Revises: 0051_add_tryon_lifecycle_and_attempts
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0052_add_tryon_reliability_events_and_dlq"
down_revision: str | None = "0051_add_tryon_lifecycle_and_attempts"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Add reliability and lease columns to tryon_jobs
    op.add_column("tryon_jobs", sa.Column("version", sa.Integer(), server_default="1", nullable=False))
    op.add_column("tryon_jobs", sa.Column("retry_count", sa.Integer(), server_default="0", nullable=False))
    op.add_column("tryon_jobs", sa.Column("max_retries", sa.Integer(), server_default="3", nullable=False))
    op.add_column("tryon_jobs", sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("tryon_jobs", sa.Column("last_error_code", sa.String(length=64), nullable=True))
    op.add_column("tryon_jobs", sa.Column("last_error_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("tryon_jobs", sa.Column("worker_id", sa.String(length=255), nullable=True))
    op.add_column("tryon_jobs", sa.Column("lease_token", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("tryon_jobs", sa.Column("lease_expires_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("tryon_jobs", sa.Column("heartbeat_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("tryon_jobs", sa.Column("deadline_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("tryon_jobs", sa.Column("cancel_requested_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("tryon_jobs", sa.Column("failed_at", sa.DateTime(timezone=True), nullable=True))

    op.create_index(
        "ix_tryon_jobs_recovery",
        "tryon_jobs",
        ["status", "next_retry_at", "lease_expires_at"],
    )
    op.create_index(
        "ix_tryon_jobs_stale",
        "tryon_jobs",
        ["status", "heartbeat_at"],
    )

    # 2. Create tryon_job_events table
    op.create_table(
        "tryon_job_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "job_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tryon_jobs.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("from_state", sa.String(length=50), nullable=True),
        sa.Column("to_state", sa.String(length=50), nullable=False),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("reason_code", sa.String(length=64), nullable=True),
        sa.Column("actor_type", sa.String(length=32), nullable=False),
        sa.Column("worker_id", sa.String(length=255), nullable=True),
        sa.Column("attempt_number", sa.Integer(), nullable=True),
        sa.Column(
            "metadata_json",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_tryon_job_events_job_time",
        "tryon_job_events",
        ["job_id", "created_at"],
    )

    # 3. Create tryon_dead_letters table
    op.create_table(
        "tryon_dead_letters",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "job_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tryon_jobs.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        sa.Column("source", sa.String(length=100), nullable=False),
        sa.Column("failure_stage", sa.String(length=50), nullable=False),
        sa.Column("error_code", sa.String(length=64), nullable=False),
        sa.Column("error_summary", sa.String(length=500), nullable=False),
        sa.Column("attempt_number", sa.Integer(), server_default="0", nullable=False),
        sa.Column("original_message_id", sa.String(length=255), nullable=True),
        sa.Column(
            "payload_reference",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("status", sa.String(length=32), server_default="OPEN", nullable=False, index=True),
        sa.Column("resolution_note", sa.Text(), nullable=True),
        sa.Column("resolved_by", sa.String(length=100), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('OPEN', 'INVESTIGATING', 'REPLAYED', 'DISCARDED', 'RESOLVED')",
            name="ck_tryon_dlq_status",
        ),
        sa.CheckConstraint("attempt_number >= 0", name="ck_tryon_dlq_attempt_nonnegative"),
    )
    op.create_index(
        "ix_tryon_dead_letters_status_created",
        "tryon_dead_letters",
        ["status", "created_at"],
    )


def downgrade() -> None:
    # 3. Drop tryon_dead_letters
    op.drop_table("tryon_dead_letters")

    # 2. Drop tryon_job_events
    op.drop_table("tryon_job_events")

    # 1. Drop added indexes and columns from tryon_jobs
    op.drop_index("ix_tryon_jobs_stale", table_name="tryon_jobs")
    op.drop_index("ix_tryon_jobs_recovery", table_name="tryon_jobs")

    op.drop_column("tryon_jobs", "failed_at")
    op.drop_column("tryon_jobs", "cancel_requested_at")
    op.drop_column("tryon_jobs", "deadline_at")
    op.drop_column("tryon_jobs", "heartbeat_at")
    op.drop_column("tryon_jobs", "lease_expires_at")
    op.drop_column("tryon_jobs", "lease_token")
    op.drop_column("tryon_jobs", "worker_id")
    op.drop_column("tryon_jobs", "last_error_at")
    op.drop_column("tryon_jobs", "last_error_code")
    op.drop_column("tryon_jobs", "next_retry_at")
    op.drop_column("tryon_jobs", "max_retries")
    op.drop_column("tryon_jobs", "retry_count")
    op.drop_column("tryon_jobs", "version")
