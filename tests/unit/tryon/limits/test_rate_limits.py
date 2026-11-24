"""Unit tests for user and merchant rate limiters and concurrency enforcement (Phase 07.6).

Covers RATE-001 through RATE-008.
"""

from __future__ import annotations

import uuid

import pytest

from backend.fashx.tryon.limits.merchant_limits import MerchantRateLimiter
from backend.fashx.tryon.limits.redis_limiter import SlidingWindowRateLimiter
from backend.fashx.tryon.limits.user_limits import (
    TryOnRateLimitExceeded,
    UserRateLimiter,
)


@pytest.mark.asyncio
async def test_user_within_burst_limit_succeeds():
    """RATE-001: Shopper permitted to make up to 5 requests in 10-minute window."""
    limiter = SlidingWindowRateLimiter(redis_client=None)
    user_limiter = UserRateLimiter(limiter)
    user_id = uuid.uuid4()

    # Make 5 requests, releasing concurrency each time
    for _ in range(5):
        job_id = uuid.uuid4()
        await user_limiter.check_and_acquire(user_id, job_id)
        await user_limiter.release_concurrency(user_id, job_id)


@pytest.mark.asyncio
async def test_user_burst_limit_rejection():
    """RATE-002: Shopper rejected with USER_BURST_10M on 6th request."""
    limiter = SlidingWindowRateLimiter(redis_client=None)
    user_limiter = UserRateLimiter(limiter)
    user_id = uuid.uuid4()

    for _ in range(5):
        job_id = uuid.uuid4()
        await user_limiter.check_and_acquire(user_id, job_id)
        await user_limiter.release_concurrency(user_id, job_id)

    # 6th request fails
    with pytest.raises(TryOnRateLimitExceeded) as exc_info:
        await user_limiter.check_and_acquire(user_id, uuid.uuid4())

    err = exc_info.value
    assert err.limit_type == "USER_BURST_10M"
    assert err.limit == 5
    assert err.retry_after > 0


@pytest.mark.asyncio
async def test_user_daily_limit_rejection():
    """RATE-003: Shopper rejected with USER_DAILY_24H on 21st request."""
    limiter = SlidingWindowRateLimiter(redis_client=None)
    user_limiter = UserRateLimiter(limiter)
    user_id = uuid.uuid4()

    # Pre-populate 20 timestamps in daily window
    key = f"tryon:ratelimit:user:day:{user_id}"
    for _ in range(20):
        await limiter.check_rate_limit(key, limit=20, window_seconds=86400)

    with pytest.raises(TryOnRateLimitExceeded) as exc_info:
        await user_limiter.check_and_acquire(user_id, uuid.uuid4())

    err = exc_info.value
    assert err.limit_type == "USER_DAILY_24H"
    assert err.limit == 20


@pytest.mark.asyncio
async def test_user_concurrency_ceiling():
    """RATE-004: Shopper cannot exceed 2 active jobs concurrently."""
    limiter = SlidingWindowRateLimiter(redis_client=None)
    user_limiter = UserRateLimiter(limiter)
    user_id = uuid.uuid4()

    job1 = uuid.uuid4()
    job2 = uuid.uuid4()
    job3 = uuid.uuid4()

    # Acquire slot 1 and 2 (without releasing)
    await user_limiter.check_and_acquire(user_id, job1)
    await user_limiter.check_and_acquire(user_id, job2)

    # 3rd concurrent request should fail
    with pytest.raises(TryOnRateLimitExceeded) as exc_info:
        await user_limiter.check_and_acquire(user_id, job3)

    err = exc_info.value
    assert err.limit_type == "USER_CONCURRENCY"
    assert err.limit == 2


@pytest.mark.asyncio
async def test_user_concurrency_release():
    """RATE-005: Releasing an active job slot allows subsequent job acquisition."""
    limiter = SlidingWindowRateLimiter(redis_client=None)
    user_limiter = UserRateLimiter(limiter)
    user_id = uuid.uuid4()

    job1 = uuid.uuid4()
    job2 = uuid.uuid4()
    job3 = uuid.uuid4()

    await user_limiter.check_and_acquire(user_id, job1)
    await user_limiter.check_and_acquire(user_id, job2)

    # Release job 1
    await user_limiter.release_concurrency(user_id, job1)

    # Now job 3 should succeed
    await user_limiter.check_and_acquire(user_id, job3)


@pytest.mark.asyncio
async def test_merchant_rate_burst():
    """RATE-006: Merchant rejected with MERCHANT_BURST_1M on 61st request."""
    limiter = SlidingWindowRateLimiter(redis_client=None)
    merchant_limiter = MerchantRateLimiter(limiter)
    merchant_id = uuid.uuid4()

    # Pre-populate 60 requests in 1m window
    key = f"tryon:ratelimit:merchant:1m:{merchant_id}"
    for _ in range(60):
        await limiter.check_rate_limit(key, limit=60, window_seconds=60)

    with pytest.raises(TryOnRateLimitExceeded) as exc_info:
        await merchant_limiter.check_and_acquire(merchant_id, uuid.uuid4())

    err = exc_info.value
    assert err.limit_type == "MERCHANT_BURST_1M"
    assert err.limit == 60


@pytest.mark.asyncio
async def test_merchant_concurrency_ceiling():
    """RATE-007: Merchant concurrency capped at 20 active jobs."""
    limiter = SlidingWindowRateLimiter(redis_client=None)
    merchant_limiter = MerchantRateLimiter(limiter)
    merchant_id = uuid.uuid4()

    for _ in range(20):
        await merchant_limiter.check_and_acquire(merchant_id, uuid.uuid4())

    with pytest.raises(TryOnRateLimitExceeded) as exc_info:
        await merchant_limiter.check_and_acquire(merchant_id, uuid.uuid4())

    err = exc_info.value
    assert err.limit_type == "MERCHANT_CONCURRENCY"
    assert err.limit == 20


def test_rate_limit_exceeded_payload_and_headers():
    """RATE-008: Error headers and JSON serialization follow RFC standards."""
    exc = TryOnRateLimitExceeded(
        message="Too many requests",
        limit_type="USER_BURST_10M",
        limit=5,
        retry_after=42,
    )
    headers = exc.as_headers()
    assert headers["Retry-After"] == "42"
    assert headers["X-RateLimit-Limit"] == "5"
    assert headers["X-RateLimit-Type"] == "USER_BURST_10M"

    data = exc.as_json()
    assert data["error"] == "rate_limit_exceeded"
    assert data["retry_after_seconds"] == 42
