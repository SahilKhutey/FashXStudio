from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, UUIDPrimaryKeyMixin


class TryOnJob(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "tryon_jobs"
    __table_args__ = (
        Index("ix_tryon_jobs_user_id", "user_id", "created_at"),
        UniqueConstraint("user_id", "idempotency_key", name="uq_tryon_user_idempotency"),
        UniqueConstraint("artifact_key", name="uq_tryon_jobs_artifact_key"),
    )

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    garment_id: Mapped[UUID] = mapped_column(
        ForeignKey("canonical_garments.id", ondelete="CASCADE")
    )
    profile_photo_id: Mapped[UUID] = mapped_column(ForeignKey("user_photos.id", ondelete="CASCADE"))
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False)
    artifact_key: Mapped[str] = mapped_column(String(512), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="queued", nullable=False)
    model_version: Mapped[str] = mapped_column(String(64), nullable=False)
    pipeline_version: Mapped[str] = mapped_column(String(64), nullable=False)
    failure_reason: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    attempts: Mapped[int] = mapped_column(default=1, nullable=False)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    photo_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    garment_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    configuration_hash: Mapped[str] = mapped_column(String(128), default="default", nullable=False)
    queue_name: Mapped[str] = mapped_column(String(128), default="tryon-jobs", nullable=False)
    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    locked_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    cancel_requested: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_error: Mapped[str | None] = mapped_column(Text)
    provider: Mapped[str | None] = mapped_column(Text, nullable=True)
    provider_job_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    request_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    provider_submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    provider_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    validation_policy_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    progress_stage: Mapped[str | None] = mapped_column(String(64), default="waiting_for_worker", nullable=True)
    lock_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_retries: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    next_retry_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_error_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    worker_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    lease_token: Mapped[UUID | None] = mapped_column(nullable=True)
    lease_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deadline_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancel_requested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class TryOnArtifact(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "tryon_artifacts"

    job_id: Mapped[UUID] = mapped_column(
        ForeignKey("tryon_jobs.id", ondelete="CASCADE"), unique=True
    )
    artifact_key: Mapped[str] = mapped_column(String(512), unique=True, nullable=False)
    result_key: Mapped[str] = mapped_column(Text, nullable=False)
    model_version: Mapped[str] = mapped_column(String(64), nullable=False)
    pipeline_version: Mapped[str] = mapped_column(String(64), nullable=False)
    photo_version: Mapped[int] = mapped_column(nullable=False)
    garment_version: Mapped[int] = mapped_column(nullable=False)
    quality_status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)
    quality_score: Mapped[float | None] = mapped_column(Float)
    width: Mapped[int | None] = mapped_column(Integer)
    height: Mapped[int | None] = mapped_column(Integer)
    size_bytes: Mapped[int | None] = mapped_column(Integer)
    content_type: Mapped[str | None] = mapped_column(String(64))
    content_sha256: Mapped[str | None] = mapped_column(String(64), index=True)
    quality_reasons: Mapped[list[str] | None] = mapped_column(JSON, default=list, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    provider: Mapped[str | None] = mapped_column(String(64), nullable=True)
    provider_model_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    source_image_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    garment_image_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    output_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    processing_latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    @property
    def safe_quality_reasons(self) -> list[str]:
        return self.quality_reasons or []


class TryOnUsage(Base, UUIDPrimaryKeyMixin):
    """Cost and vendor tracking table. Deliberately has NO user_id or job_id for privacy."""

    __tablename__ = "tryon_usage"

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    provider: Mapped[str] = mapped_column(Text, nullable=False)
    model: Mapped[str] = mapped_column(Text, nullable=False)
    outcome: Mapped[str] = mapped_column(
        Text, nullable=False
    )  # completed | failed | retried | cancelled
    error_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(nullable=True)
    cost_usd_est: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)

    __table_args__ = (Index("ix_tryon_usage_created", "created_at"),)


class TryOnInputValidation(Base, UUIDPrimaryKeyMixin):
    """Immutable audit record of image validation outcomes for a tryon job (Phase 07.3)."""

    __tablename__ = "tryon_input_validations"
    __table_args__ = (
        Index("ix_tryon_input_job", "tryon_job_id"),
        Index("ix_tryon_input_asset", "asset_id", "asset_version"),
        Index("ix_tryon_input_status", "status", "validated_at"),
        UniqueConstraint(
            "tryon_job_id",
            "role",
            "asset_id",
            "asset_version",
            "policy_version",
            name="uq_tryon_input_validations_idempotency",
        ),
    )

    tryon_job_id: Mapped[UUID] = mapped_column(
        ForeignKey("tryon_jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    asset_id: Mapped[UUID] = mapped_column(nullable=False)
    asset_version: Mapped[str] = mapped_column(String(64), nullable=False)
    original_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    normalized_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    policy_version: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    technical_metadata: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    visual_metadata: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    issues: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    validated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class TryOnInputAuthorizationSnapshot(Base, UUIDPrimaryKeyMixin):
    """Time-of-check authorization and consent snapshot for a tryon job (Phase 07.3)."""

    __tablename__ = "tryon_input_authorization_snapshots"
    __table_args__ = (
        Index("ix_tryon_auth_snapshot_job", "tryon_job_id"),
        Index("ix_tryon_auth_snapshot_subject", "subject_id", "authorization_type"),
    )

    tryon_job_id: Mapped[UUID] = mapped_column(
        ForeignKey("tryon_jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    authorization_type: Mapped[str] = mapped_column(String(32), nullable=False)
    subject_id: Mapped[UUID] = mapped_column(nullable=False)
    permission_scope: Mapped[str] = mapped_column(String(64), nullable=False)
    evidence_revision: Mapped[str | None] = mapped_column(String(64), nullable=True)
    policy_version: Mapped[str] = mapped_column(String(32), nullable=False)
    checked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    result: Mapped[str] = mapped_column(String(32), nullable=False)


class TryOnProviderAttempt(Base, UUIDPrimaryKeyMixin):
    """Auditable record of an inference attempt dispatched to a third-party VTO provider (Phase 07.4)."""

    __tablename__ = "tryon_provider_attempts"
    __table_args__ = (
        Index("ix_tryon_provider_attempt_job", "job_id"),
        Index("ix_tryon_provider_attempt_status", "status", "created_at"),
        Index("ix_tryon_provider_attempt_prov_job", "provider", "provider_job_id"),
        UniqueConstraint(
            "job_id",
            "attempt_number",
            name="uq_tryon_provider_attempt_job_num",
        ),
    )

    job_id: Mapped[UUID] = mapped_column(
        ForeignKey("tryon_jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    model_version: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)  # PREPARED, SUBMITTING, ACCEPTED, UNKNOWN, COMPLETED, FAILED
    provider_job_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    request_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    provider_error_code: Mapped[str | None] = mapped_column(String(128), nullable=True)
    safe_error_detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class TryOnJobEvent(Base, UUIDPrimaryKeyMixin):
    """Append-only audit event for virtual try-on job state transitions (Phase 07.5)."""

    __tablename__ = "tryon_job_events"
    __table_args__ = (
        Index("ix_tryon_job_events_job_time", "job_id", "created_at"),
    )

    job_id: Mapped[UUID] = mapped_column(
        ForeignKey("tryon_jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    from_state: Mapped[str | None] = mapped_column(String(50), nullable=True)
    to_state: Mapped[str] = mapped_column(String(50), nullable=False)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    reason_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    actor_type: Mapped[str] = mapped_column(String(32), nullable=False)
    worker_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    attempt_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class TryOnDeadLetter(Base, UUIDPrimaryKeyMixin):
    """Durable record of failed jobs, exhausted retries, or corrupt payloads for operational triage (Phase 07.5)."""

    __tablename__ = "tryon_dead_letters"
    __table_args__ = (
        Index("ix_tryon_dead_letters_status_created", "status", "created_at"),
        Index("ix_tryon_dead_letters_job", "job_id"),
    )

    job_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("tryon_jobs.id", ondelete="SET NULL"), nullable=True, index=True
    )
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    failure_stage: Mapped[str] = mapped_column(String(50), nullable=False)
    error_code: Mapped[str] = mapped_column(String(64), nullable=False)
    error_summary: Mapped[str] = mapped_column(String(500), nullable=False)
    attempt_number: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    original_message_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    payload_reference: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="OPEN", nullable=False, index=True)
    resolution_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolved_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


