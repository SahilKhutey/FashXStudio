"""Infrastructure tests for Redis resilience, error handling, and fallback behavior.

Validates that dependency checks, rate limiting, and release validation gracefully
handle connection timeouts and misconfigurations.
"""

from __future__ import annotations

import pytest

from fashx.health.router import check_redis_dependency
from fashx.security.ratelimit import RedisRateLimiter


@pytest.mark.asyncio
async def test_check_redis_dependency_returns_false_on_unreachable_endpoint() -> None:
    # Pointing to an invalid endpoint should timeout and safely return False
    unreachable_url = "redis://127.0.0.1:59999/0"
    result = await check_redis_dependency(unreachable_url)
    assert result is False, "Health check should report False when Redis is unreachable"


@pytest.mark.asyncio
async def test_redis_rate_limiter_falls_back_gracefully_when_offline() -> None:
    # When pointed at unreachable Redis, RedisRateLimiter falls back to InMemoryRateLimiter
    unreachable_url = "redis://127.0.0.1:59999/0"
    limiter = RedisRateLimiter(unreachable_url)

    # First request should pass under limit
    res1 = await limiter.check("test_key_resilience", max_requests=2, window_seconds=60)
    assert res1.allowed is True

    # Second request should pass under limit
    res2 = await limiter.check("test_key_resilience", max_requests=2, window_seconds=60)
    assert res2.allowed is True

    # Third request should be blocked by fallback limiter
    res3 = await limiter.check("test_key_resilience", max_requests=2, window_seconds=60)
    assert res3.allowed is False
    assert res3.remaining == 0

