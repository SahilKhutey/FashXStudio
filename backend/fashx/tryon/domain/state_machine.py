"""VTO Job State Machine and Transition Rules (Phase 07.4)."""

from __future__ import annotations

from enum import StrEnum


class JobStatus(StrEnum):
    QUEUED = "queued"
    VALIDATING = "validating"
    READY_FOR_PROVIDER = "ready_for_provider"
    SUBMITTING = "submitting"
    SUBMISSION_UNKNOWN = "submission_unknown"
    SUBMITTED = "submitted"
    PROCESSING = "processing"
    DOWNLOADING = "downloading"
    VALIDATING_OUTPUT = "validating_output"
    STORING_RESULT = "storing_result"
    # Terminal states
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    BLOCKED_BY_PERMISSION = "blocked_by_permission"


class ProgressStage(StrEnum):
    WAITING_FOR_WORKER = "waiting_for_worker"
    VALIDATING_INPUTS = "validating_inputs"
    READY_FOR_PROVIDER = "ready_for_provider"
    SUBMITTING_TO_PROVIDER = "submitting_to_provider"
    SUBMISSION_UNKNOWN = "submission_unknown"
    PROVIDER_INFERENCE = "provider_inference"
    RETRIEVING_OUTPUT = "retrieving_output"
    VALIDATING_OUTPUT = "validating_output"
    STORING_RESULT = "storing_result"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    BLOCKED_BY_PERMISSION = "blocked_by_permission"


class ProviderAttemptStatus(StrEnum):
    PREPARED = "PREPARED"
    SUBMITTING = "SUBMITTING"
    ACCEPTED = "ACCEPTED"
    UNKNOWN = "UNKNOWN"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


TERMINAL_STATUSES: frozenset[JobStatus] = frozenset({
    JobStatus.COMPLETED,
    JobStatus.FAILED,
    JobStatus.CANCELLED,
    JobStatus.BLOCKED_BY_PERMISSION,
})

LEGAL_TRANSITIONS: dict[JobStatus, frozenset[JobStatus]] = {
    JobStatus.QUEUED: frozenset({
        JobStatus.VALIDATING,
        JobStatus.CANCELLED,
    }),
    JobStatus.VALIDATING: frozenset({
        JobStatus.READY_FOR_PROVIDER,
        JobStatus.FAILED,
        JobStatus.BLOCKED_BY_PERMISSION,
        JobStatus.CANCELLED,
    }),
    JobStatus.READY_FOR_PROVIDER: frozenset({
        JobStatus.SUBMITTING,
        JobStatus.CANCELLED,
        JobStatus.BLOCKED_BY_PERMISSION,
    }),
    JobStatus.SUBMITTING: frozenset({
        JobStatus.SUBMITTED,
        JobStatus.SUBMISSION_UNKNOWN,
        JobStatus.FAILED,
    }),
    JobStatus.SUBMISSION_UNKNOWN: frozenset({
        JobStatus.SUBMITTED,
        JobStatus.PROCESSING,
        JobStatus.FAILED,
        JobStatus.BLOCKED_BY_PERMISSION,
    }),
    JobStatus.SUBMITTED: frozenset({
        JobStatus.PROCESSING,
        JobStatus.DOWNLOADING,
        JobStatus.FAILED,
    }),
    JobStatus.PROCESSING: frozenset({
        JobStatus.PROCESSING,
        JobStatus.DOWNLOADING,
        JobStatus.FAILED,
        JobStatus.CANCELLED,
    }),
    JobStatus.DOWNLOADING: frozenset({
        JobStatus.VALIDATING_OUTPUT,
        JobStatus.FAILED,
    }),
    JobStatus.VALIDATING_OUTPUT: frozenset({
        JobStatus.STORING_RESULT,
        JobStatus.FAILED,
    }),
    JobStatus.STORING_RESULT: frozenset({
        JobStatus.COMPLETED,
        JobStatus.FAILED,
    }),
    # Terminal states allow no further transitions
    JobStatus.COMPLETED: frozenset(),
    JobStatus.FAILED: frozenset(),
    JobStatus.CANCELLED: frozenset(),
    JobStatus.BLOCKED_BY_PERMISSION: frozenset(),
}


class InvalidJobTransitionError(Exception):
    """Raised when an illegal state transition is attempted."""

    def __init__(self, from_status: str | JobStatus, to_status: str | JobStatus) -> None:
        self.from_status = str(from_status)
        self.to_status = str(to_status)
        super().__init__(
            f"Illegal job state transition: cannot transition from '{self.from_status}' to '{self.to_status}'"
        )


def is_terminal_status(status: str | JobStatus) -> bool:
    """Returns True if the given status is a terminal state."""
    try:
        s = JobStatus(str(status))
        return s in TERMINAL_STATUSES
    except ValueError:
        return False


def validate_transition(current_status: str | JobStatus, target_status: str | JobStatus) -> None:
    """Validates that transitioning from current_status to target_status is permitted by the state machine."""
    try:
        curr = JobStatus(str(current_status))
        tgt = JobStatus(str(target_status))
    except ValueError as exc:
        raise InvalidJobTransitionError(current_status, target_status) from exc

    allowed = LEGAL_TRANSITIONS.get(curr, frozenset())
    if tgt not in allowed:
        raise InvalidJobTransitionError(curr, tgt)
