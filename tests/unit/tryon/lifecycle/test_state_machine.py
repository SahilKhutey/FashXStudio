"""Unit tests for VTO Job State Machine and legal transition enforcement (Phase 07.4)."""

from __future__ import annotations

import pytest

from fashx.tryon.domain.state_machine import (
    InvalidJobTransitionError,
    JobStatus,
    is_terminal_status,
    validate_transition,
)


def test_legal_forward_transitions() -> None:
    # QUEUED -> VALIDATING
    validate_transition(JobStatus.QUEUED, JobStatus.VALIDATING)
    # VALIDATING -> READY_FOR_PROVIDER
    validate_transition(JobStatus.VALIDATING, JobStatus.READY_FOR_PROVIDER)
    # READY_FOR_PROVIDER -> SUBMITTING
    validate_transition(JobStatus.READY_FOR_PROVIDER, JobStatus.SUBMITTING)
    # SUBMITTING -> SUBMITTED
    validate_transition(JobStatus.SUBMITTING, JobStatus.SUBMITTED)
    # SUBMITTED -> DOWNLOADING
    validate_transition(JobStatus.SUBMITTED, JobStatus.DOWNLOADING)
    # DOWNLOADING -> VALIDATING_OUTPUT
    validate_transition(JobStatus.DOWNLOADING, JobStatus.VALIDATING_OUTPUT)
    # VALIDATING_OUTPUT -> STORING_RESULT
    validate_transition(JobStatus.VALIDATING_OUTPUT, JobStatus.STORING_RESULT)
    # STORING_RESULT -> COMPLETED
    validate_transition(JobStatus.STORING_RESULT, JobStatus.COMPLETED)


def test_submission_unknown_recovery_transitions() -> None:
    # SUBMITTING -> SUBMISSION_UNKNOWN
    validate_transition(JobStatus.SUBMITTING, JobStatus.SUBMISSION_UNKNOWN)
    # SUBMISSION_UNKNOWN -> SUBMITTED (recovered provider ID)
    validate_transition(JobStatus.SUBMISSION_UNKNOWN, JobStatus.SUBMITTED)
    # SUBMISSION_UNKNOWN -> FAILED (reconciliation exhausted)
    validate_transition(JobStatus.SUBMISSION_UNKNOWN, JobStatus.FAILED)


def test_permission_block_transitions() -> None:
    # VALIDATING -> BLOCKED_BY_PERMISSION
    validate_transition(JobStatus.VALIDATING, JobStatus.BLOCKED_BY_PERMISSION)
    # READY_FOR_PROVIDER -> BLOCKED_BY_PERMISSION
    validate_transition(JobStatus.READY_FOR_PROVIDER, JobStatus.BLOCKED_BY_PERMISSION)


def test_illegal_jump_transitions_raise_error() -> None:
    # Cannot jump directly from QUEUED to COMPLETED
    with pytest.raises(InvalidJobTransitionError):
        validate_transition(JobStatus.QUEUED, JobStatus.COMPLETED)

    # Cannot jump from VALIDATING to STORING_RESULT
    with pytest.raises(InvalidJobTransitionError):
        validate_transition(JobStatus.VALIDATING, JobStatus.STORING_RESULT)


def test_terminal_states_cannot_transition() -> None:
    assert is_terminal_status(JobStatus.COMPLETED)
    assert is_terminal_status(JobStatus.FAILED)
    assert is_terminal_status(JobStatus.CANCELLED)
    assert is_terminal_status(JobStatus.BLOCKED_BY_PERMISSION)

    with pytest.raises(InvalidJobTransitionError):
        validate_transition(JobStatus.COMPLETED, JobStatus.QUEUED)

    with pytest.raises(InvalidJobTransitionError):
        validate_transition(JobStatus.FAILED, JobStatus.SUBMITTING)
