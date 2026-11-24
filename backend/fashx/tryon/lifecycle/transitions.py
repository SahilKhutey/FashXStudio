"""VTO Job State Transition Matrix and Validation (Phase 07.5)."""

from __future__ import annotations

from fashx.tryon.lifecycle.states import (
    TERMINAL_STATES,
    JobStatus,
    normalize_job_status,
)


class InvalidJobTransition(ValueError):
    """Raised when an illegal state machine transition is attempted."""

    def __init__(self, current_status: JobStatus, target_status: JobStatus) -> None:
        self.current_status = current_status
        self.target_status = target_status
        super().__init__(
            f"Illegal job state transition: cannot transition from {current_status.value} to {target_status.value}"
        )


ALLOWED_TRANSITIONS: dict[JobStatus, frozenset[JobStatus]] = {
    JobStatus.CREATED: frozenset({
        JobStatus.VALIDATING,
        JobStatus.CANCELLED,
        JobStatus.FAILED,
    }),
    JobStatus.VALIDATING: frozenset({
        JobStatus.QUEUED,
        JobStatus.FAILED,
        JobStatus.CANCEL_REQUESTED,
        JobStatus.CANCELLED,
    }),
    JobStatus.QUEUED: frozenset({
        JobStatus.PROCESSING,
        JobStatus.CANCELLED,
        JobStatus.FAILED,
    }),
    JobStatus.PROCESSING: frozenset({
        JobStatus.SUBMISSION_UNKNOWN,
        JobStatus.RETRY_PENDING,
        JobStatus.OUTPUT_VALIDATING,
        JobStatus.CANCEL_REQUESTED,
        JobStatus.FAILED,
    }),
    JobStatus.SUBMISSION_UNKNOWN: frozenset({
        JobStatus.PROCESSING,
        JobStatus.RETRY_PENDING,
        JobStatus.FAILED,
        JobStatus.CANCEL_REQUESTED,
    }),
    JobStatus.RETRY_PENDING: frozenset({
        JobStatus.PROCESSING,
        JobStatus.CANCELLED,
        JobStatus.FAILED,
    }),
    JobStatus.OUTPUT_VALIDATING: frozenset({
        JobStatus.STORING_RESULT,
        JobStatus.FAILED,
        JobStatus.CANCEL_REQUESTED,
    }),
    JobStatus.STORING_RESULT: frozenset({
        JobStatus.COMPLETED,
        JobStatus.FAILED,
        JobStatus.CANCEL_REQUESTED,
    }),
    JobStatus.CANCEL_REQUESTED: frozenset({
        JobStatus.CANCELLED,
        JobStatus.FAILED,
        JobStatus.COMPLETED,
    }),
    JobStatus.COMPLETED: frozenset({
        JobStatus.EXPIRED,
    }),
    JobStatus.FAILED: frozenset(),
    JobStatus.CANCELLED: frozenset(),
    JobStatus.EXPIRED: frozenset(),
}


def validate_transition(
    current: str | JobStatus,
    target: str | JobStatus,
) -> tuple[JobStatus, JobStatus]:
    """Validate that transition from current to target status is strictly legal.

    Raises InvalidJobTransition if the jump is forbidden.
    """
    curr_enum = normalize_job_status(current)
    target_enum = normalize_job_status(target)

    # Identical transition is a no-op if not terminal
    if curr_enum == target_enum and curr_enum not in TERMINAL_STATES:
        return curr_enum, target_enum

    allowed = ALLOWED_TRANSITIONS.get(curr_enum, frozenset())
    if target_enum not in allowed:
        raise InvalidJobTransition(curr_enum, target_enum)

    return curr_enum, target_enum
