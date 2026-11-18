"""SA-010: Token bucket rate limiting and 429 Retry-After handling."""

from __future__ import annotations

import time

import pytest

from fashx.catalog.acquisition.rate_limiter import DistributedRateLimiter


@pytest.mark.asyncio
async def test_sa_010_token_bucket_acquire() -> None:
    """SA-010: Token bucket allows burst up to capacity and throttles sustained requests."""
    limiter = DistributedRateLimiter()

    # 5 immediate acquires should be instantaneous
    t0 = time.monotonic()
    for _ in range(5):
        await limiter.acquire(key="source-1", max_rps=5.0)
    elapsed = time.monotonic() - t0
    assert elapsed < 0.1  # Fast burst

    # The 6th request requires token replenishment (at 5.0 rps, ~0.2s delay)
    t1 = time.monotonic()
    await limiter.acquire(key="source-1", max_rps=5.0)
    elapsed_replenish = time.monotonic() - t1
    assert elapsed_replenish >= 0.15


@pytest.mark.asyncio
async def test_sa_010_retry_after_handling() -> None:
    """SA-010: 429 Retry-After sets explicit backoff delay."""
    limiter = DistributedRateLimiter()

    # Set Retry-After for 0.25 seconds
    await limiter.record_retry_after(key="source-2", seconds=0.25)

    t0 = time.monotonic()
    await limiter.acquire(key="source-2", max_rps=10.0)
    elapsed = time.monotonic() - t0
    assert elapsed >= 0.20
