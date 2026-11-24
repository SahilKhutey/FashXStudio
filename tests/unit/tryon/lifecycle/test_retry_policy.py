"""Unit tests for VTO Error Classification, Retry Policy, and Backoff Calculation (Phase 07.5).

Covers RET-001 through RET-015.
"""

from __future__ import annotations

import pytest

from fashx.tryon.lifecycle.errors import (
    ErrorCategory,
    ErrorCode,
    classify_error,
)
from fashx.tryon.lifecycle.retry_policy import (
    OUTPUT_DOWNLOAD_POLICY,
    PROVIDER_POLLING_POLICY,
    PROVIDER_SUBMISSION_UNKNOWN_POLICY,
    STORAGE_UPLOAD_POLICY,
    WORKER_EXECUTION_POLICY,
    RetryPolicy,
    calculate_retry_delay,
    retry_allowed,
)


def test_retryable_error_eligible() -> None:
    # RET-001
    defn = classify_error(ErrorCode.PROVIDER_UNAVAILABLE)
    assert defn.category == ErrorCategory.TRANSIENT
    assert defn.retryable is True
    assert defn.safe_to_repeat is True
    assert retry_allowed(
        retry_count=1,
        policy=WORKER_EXECUTION_POLICY,
        retryable=defn.retryable,
        safe_to_repeat=defn.safe_to_repeat,
    )


def test_permanent_error_not_retried() -> None:
    # RET-002
    defn = classify_error(ErrorCode.INVALID_INPUT_IMAGE)
    assert defn.category == ErrorCategory.PERMANENT
    assert defn.retryable is False
    assert not retry_allowed(
        retry_count=0,
        policy=WORKER_EXECUTION_POLICY,
        retryable=defn.retryable,
        safe_to_repeat=defn.safe_to_repeat,
    )


def test_configuration_error_not_retried() -> None:
    # RET-003
    defn = classify_error(ErrorCode.PROVIDER_AUTH_FAILED)
    assert defn.category == ErrorCategory.CONFIGURATION
    assert defn.retryable is False
    assert not retry_allowed(
        retry_count=0,
        policy=WORKER_EXECUTION_POLICY,
        retryable=defn.retryable,
        safe_to_repeat=defn.safe_to_repeat,
    )


def test_ambiguous_provider_submission_not_blindly_retried() -> None:
    # RET-004
    defn = classify_error(ErrorCode.PROVIDER_SUBMISSION_UNKNOWN)
    assert defn.category == ErrorCategory.AMBIGUOUS
    assert defn.retryable is False
    assert defn.safe_to_repeat is False
    assert not retry_allowed(
        retry_count=0,
        policy=PROVIDER_SUBMISSION_UNKNOWN_POLICY,
        retryable=defn.retryable,
        safe_to_repeat=defn.safe_to_repeat,
    )


def test_retry_count_below_maximum_allowed() -> None:
    # RET-005
    policy = RetryPolicy(max_retries=3)
    assert retry_allowed(retry_count=2, policy=policy, retryable=True, safe_to_repeat=True)


def test_retry_count_equals_or_exceeds_maximum_denied() -> None:
    # RET-006
    policy = RetryPolicy(max_retries=3)
    assert not retry_allowed(retry_count=3, policy=policy, retryable=True, safe_to_repeat=True)
    assert not retry_allowed(retry_count=4, policy=policy, retryable=True, safe_to_repeat=True)


def test_exponential_backoff_progression() -> None:
    # RET-007
    policy = RetryPolicy(initial_delay_seconds=2.0, maximum_delay_seconds=100.0, jitter_enabled=False)
    # n=0 -> 2.0 * 2^0 = 2.0
    # n=1 -> 2.0 * 2^1 = 4.0
    # n=2 -> 2.0 * 2^2 = 8.0
    # n=3 -> 2.0 * 2^3 = 16.0
    assert calculate_retry_delay(0, policy) == 2.0
    assert calculate_retry_delay(1, policy) == 4.0
    assert calculate_retry_delay(2, policy) == 8.0
    assert calculate_retry_delay(3, policy) == 16.0


def test_backoff_cap_enforced() -> None:
    # RET-008
    policy = RetryPolicy(initial_delay_seconds=5.0, maximum_delay_seconds=20.0, jitter_enabled=False)
    # n=5 -> 5.0 * 32 = 160.0 -> capped at 20.0
    assert calculate_retry_delay(5, policy) == 20.0


def test_jitter_varies_within_configured_range() -> None:
    # RET-009: jitter between 50% and 100% of base
    policy = RetryPolicy(initial_delay_seconds=10.0, maximum_delay_seconds=100.0, jitter_enabled=True)
    # base for n=0 is 10.0 -> jitter range: [5.0, 10.0]
    delays = [calculate_retry_delay(0, policy) for _ in range(50)]
    assert all(5.0 <= d <= 10.0 for d in delays)
    # Verify randomness (not all identical)
    assert len(set(delays)) > 1


def test_provider_retry_after_respected() -> None:
    # RET-010: Provider requested 45 seconds; base is 5s
    policy = RetryPolicy(initial_delay_seconds=5.0, maximum_delay_seconds=30.0, jitter_enabled=False)
    delay = calculate_retry_delay(0, policy, retry_after_seconds=45.0)
    assert delay == 45.0  # Respects provider instruction without capping at 30s


def test_negative_retry_count_rejected() -> None:
    # RET-011
    policy = RetryPolicy(max_retries=3)
    with pytest.raises(ValueError, match="retry_number cannot be negative"):
        calculate_retry_delay(-1, policy)
    with pytest.raises(ValueError, match="retry_count cannot be negative"):
        retry_allowed(-1, policy, retryable=True, safe_to_repeat=True)


def test_unknown_error_code_not_automatically_retryable() -> None:
    # RET-012
    defn = classify_error("SOME_UNRECOGNIZED_STRANGE_ERROR")
    assert defn.code == ErrorCode.UNKNOWN_ERROR
    assert defn.category == ErrorCategory.PERMANENT
    assert defn.retryable is False
    assert not retry_allowed(
        retry_count=0,
        policy=WORKER_EXECUTION_POLICY,
        retryable=defn.retryable,
        safe_to_repeat=defn.safe_to_repeat,
    )


def test_independent_operation_budgets() -> None:
    # RET-013, RET-014, RET-015
    assert PROVIDER_POLLING_POLICY.max_retries == 8
    assert OUTPUT_DOWNLOAD_POLICY.max_retries == 4
    assert STORAGE_UPLOAD_POLICY.max_retries == 5
    assert WORKER_EXECUTION_POLICY.max_retries == 3
