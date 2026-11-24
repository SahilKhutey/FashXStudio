"""Unit tests for VTO Job State Transitions and Invalid Transition Protection (Phase 07.5).

Covers STM-001 through STM-018.
"""

from __future__ import annotations

import pytest

from fashx.tryon.lifecycle.states import JobStatus
from fashx.tryon.lifecycle.transitions import (
    InvalidJobTransition,
    validate_transition,
)


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (JobStatus.CREATED, JobStatus.VALIDATING),      # STM-001
        (JobStatus.VALIDATING, JobStatus.QUEUED),       # STM-002
        (JobStatus.QUEUED, JobStatus.PROCESSING),       # STM-003
        (JobStatus.PROCESSING, JobStatus.RETRY_PENDING), # STM-004
        (JobStatus.RETRY_PENDING, JobStatus.PROCESSING),# STM-005
        (JobStatus.PROCESSING, JobStatus.OUTPUT_VALIDATING), # STM-006
        (JobStatus.OUTPUT_VALIDATING, JobStatus.STORING_RESULT), # STM-007
        (JobStatus.STORING_RESULT, JobStatus.COMPLETED), # STM-008
        (JobStatus.PROCESSING, JobStatus.FAILED),        # STM-009
        (JobStatus.QUEUED, JobStatus.CANCELLED),        # STM-010
        (JobStatus.PROCESSING, JobStatus.SUBMISSION_UNKNOWN), # STM-011
        (JobStatus.VALIDATING, JobStatus.CANCEL_REQUESTED),
        (JobStatus.PROCESSING, JobStatus.CANCEL_REQUESTED),
        (JobStatus.SUBMISSION_UNKNOWN, JobStatus.PROCESSING),
        (JobStatus.SUBMISSION_UNKNOWN, JobStatus.FAILED),
        (JobStatus.CANCEL_REQUESTED, JobStatus.CANCELLED),
        (JobStatus.CANCEL_REQUESTED, JobStatus.FAILED),
        (JobStatus.COMPLETED, JobStatus.EXPIRED),
    ],
)
def test_allowed_transitions(current: JobStatus, target: JobStatus) -> None:
    curr_res, tgt_res = validate_transition(current, target)
    assert curr_res == current
    assert tgt_res == target


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (JobStatus.FAILED, JobStatus.PROCESSING),       # STM-012: Terminal cannot resume
        (JobStatus.CANCELLED, JobStatus.QUEUED),        # STM-013: Terminal cannot resume
        (JobStatus.COMPLETED, JobStatus.FAILED),        # STM-014: Completed cannot fail
        (JobStatus.CREATED, JobStatus.COMPLETED),       # STM-015: Illegal jump
        (JobStatus.QUEUED, JobStatus.COMPLETED),        # Illegal jump
        (JobStatus.COMPLETED, JobStatus.PROCESSING),    # Terminal cannot resume
        (JobStatus.EXPIRED, JobStatus.PROCESSING),      # Terminal cannot resume
        (JobStatus.STORING_RESULT, JobStatus.VALIDATING), # Backward jump forbidden
    ],
)
def test_rejected_transitions(current: JobStatus, target: JobStatus) -> None:
    with pytest.raises(InvalidJobTransition):
        validate_transition(current, target)


def test_unknown_status_raises_error() -> None:
    # STM-016
    with pytest.raises(ValueError, match="Unknown job status"):
        validate_transition("NON_EXISTENT_STATUS", JobStatus.QUEUED)


def test_string_representation_supported() -> None:
    curr, tgt = validate_transition("queued", "PROCESSING")
    assert curr == JobStatus.QUEUED
    assert tgt == JobStatus.PROCESSING
