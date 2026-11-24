"""VTO Operation-Specific Retry Policies, Exponential Backoff, and Jitter (Phase 07.5)."""

from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta


@dataclass(frozen=True)
class RetryPolicy:
    """Configuration governing retries for a specific operational stage."""

    max_retries: int = 3
    initial_delay_seconds: float = 5.0
    maximum_delay_seconds: float = 120.0
    jitter_enabled: bool = True
    max_operational_deferral_seconds: float = 1800.0  # 30 minutes


# Operation-specific default policies (Section 5.1)
QUEUE_DISPATCH_POLICY = RetryPolicy(
    max_retries=8,
    initial_delay_seconds=2.0,
    maximum_delay_seconds=300.0,
    jitter_enabled=True,
)

WORKER_EXECUTION_POLICY = RetryPolicy(
    max_retries=3,
    initial_delay_seconds=5.0,
    maximum_delay_seconds=120.0,
    jitter_enabled=True,
)

PROVIDER_POLLING_POLICY = RetryPolicy(
    max_retries=8,
    initial_delay_seconds=3.0,
    maximum_delay_seconds=60.0,
    jitter_enabled=True,
)

OUTPUT_DOWNLOAD_POLICY = RetryPolicy(
    max_retries=4,
    initial_delay_seconds=5.0,
    maximum_delay_seconds=60.0,
    jitter_enabled=True,
)

STORAGE_UPLOAD_POLICY = RetryPolicy(
    max_retries=5,
    initial_delay_seconds=2.0,
    maximum_delay_seconds=60.0,
    jitter_enabled=True,
)

PROVIDER_SUBMISSION_UNKNOWN_POLICY = RetryPolicy(
    max_retries=0,  # Never blind retry an ambiguous submission
    initial_delay_seconds=0.0,
    maximum_delay_seconds=0.0,
    jitter_enabled=False,
)


def calculate_retry_delay(
    retry_number: int,
    policy: RetryPolicy,
    *,
    retry_after_seconds: float | None = None,
) -> float:
    """Calculate exponential backoff delay with jitter, respecting provider Retry-After instructions.

    Formula:
        D_n = min(maximum_delay, initial_delay * 2^retry_number)
        If Retry-After is supplied: max(D_n, retry_after)
        Jitter: U(0.5 * base, base)
    """
    if retry_number < 0:
        raise ValueError("retry_number cannot be negative")

    base = min(
        policy.maximum_delay_seconds,
        policy.initial_delay_seconds * (2**retry_number),
    )

    if retry_after_seconds is not None:
        if retry_after_seconds < 0:
            raise ValueError("retry_after_seconds cannot be negative")
        # Never violate provider instruction: defer at least retry_after
        # Bounded only by maximum operational deferral
        base = min(
            max(base, retry_after_seconds),
            policy.max_operational_deferral_seconds,
        )

    if policy.jitter_enabled and base > 0:
        # Uniform jitter between 50% and 100% of delay
        return random.uniform(0.5 * base, base)

    return base


def retry_allowed(
    retry_count: int,
    policy: RetryPolicy,
    *,
    retryable: bool,
    safe_to_repeat: bool,
) -> bool:
    """Evaluate whether an operation is eligible to be retried."""
    if retry_count < 0:
        raise ValueError("retry_count cannot be negative")
    if not (retryable and safe_to_repeat):
        return False
    return retry_count < policy.max_retries


def compute_next_retry_at(
    retry_count: int,
    policy: RetryPolicy,
    *,
    retry_after_seconds: float | None = None,
    now: datetime | None = None,
) -> datetime:
    """Compute the UTC timestamp for the next retry attempt."""
    now_ts = now or datetime.now(UTC)
    delay = calculate_retry_delay(
        retry_number=retry_count,
        policy=policy,
        retry_after_seconds=retry_after_seconds,
    )
    return now_ts + timedelta(seconds=delay)
