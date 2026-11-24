"""VTO Job States and Provider Attempt States (Phase 07.5)."""

from __future__ import annotations

from enum import StrEnum


class JobStatus(StrEnum):
    """Authoritative states for a Virtual Try-On job in PostgreSQL."""

    CREATED = "CREATED"
    VALIDATING = "VALIDATING"
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    SUBMISSION_UNKNOWN = "SUBMISSION_UNKNOWN"
    RETRY_PENDING = "RETRY_PENDING"
    OUTPUT_VALIDATING = "OUTPUT_VALIDATING"
    STORING_RESULT = "STORING_RESULT"
    CANCEL_REQUESTED = "CANCEL_REQUESTED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


TERMINAL_STATES: frozenset[JobStatus] = frozenset({
    JobStatus.COMPLETED,
    JobStatus.FAILED,
    JobStatus.CANCELLED,
    JobStatus.EXPIRED,
})

ACTIVE_STATES: frozenset[JobStatus] = frozenset({
    JobStatus.CREATED,
    JobStatus.VALIDATING,
    JobStatus.QUEUED,
    JobStatus.PROCESSING,
    JobStatus.SUBMISSION_UNKNOWN,
    JobStatus.RETRY_PENDING,
    JobStatus.OUTPUT_VALIDATING,
    JobStatus.STORING_RESULT,
    JobStatus.CANCEL_REQUESTED,
})


class ProviderAttemptStatus(StrEnum):
    """Separate lifecycle status for individual outbound provider inference attempts."""

    PREPARED = "PREPARED"
    SUBMITTING = "SUBMITTING"
    ACCEPTED = "ACCEPTED"
    UNKNOWN = "UNKNOWN"
    POLLING = "POLLING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    ABANDONED = "ABANDONED"


def normalize_job_status(status: str | JobStatus) -> JobStatus:
    """Normalize string representation to canonical JobStatus enum, supporting legacy lowercase."""
    if isinstance(status, JobStatus):
        return status
    val = status.upper().strip()
    # Map legacy aliases
    alias_map = {
        "READY_FOR_PROVIDER": "QUEUED",
        "SUBMITTED": "PROCESSING",
        "SUBMITTING": "PROCESSING",
        "DOWNLOADING": "OUTPUT_VALIDATING",
        "BLOCKED_BY_PERMISSION": "FAILED",
        "PERMISSION_BLOCKED": "FAILED",
        "VALIDATION_FAILED": "FAILED",
        "QUALITY_REJECTED": "FAILED",
    }
    canonical = alias_map.get(val, val)
    try:
        return JobStatus(canonical)
    except ValueError as exc:
        raise ValueError(f"Unknown job status: {status}") from exc
