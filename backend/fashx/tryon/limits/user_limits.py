"""User / Shopper rate limiting and concurrency enforcement.

Rules:
1. Short-term window: 5 requests per 10 minutes.
2. Daily ceiling: 20 requests per 24 hours.
3. Concurrency limit: Maximum 2 concurrent in-flight jobs.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from backend.fashx.tryon.limits.redis_limiter import SlidingWindowRateLimiter


class TryOnRateLimitExceeded(Exception):
    """Raised when a shopper or merchant exceeds rate or concurrency limits."""

    def __init__(
        self,
        message: str,
        limit_type: str,
        limit: int,
        retry_after: int,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.limit_type = limit_type
        self.limit = limit
        self.retry_after = retry_after

    def as_headers(self) -> dict[str, str]:
        """Generate standard HTTP 429 rate limit headers."""
        return {
            "Retry-After": str(self.retry_after),
            "X-RateLimit-Limit": str(self.limit),
            "X-RateLimit-Type": self.limit_type,
        }

    def as_json(self) -> dict[str, Any]:
        """Generate standard API error payload."""
        return {
            "error": "rate_limit_exceeded",
            "message": self.message,
            "limit_type": self.limit_type,
            "retry_after_seconds": self.retry_after,
        }


class UserRateLimiter:
    """Enforces shopper rate and concurrency limits."""

    USER_WINDOW_10M_LIMIT = 5
    USER_WINDOW_10M_SECONDS = 600

    USER_WINDOW_DAY_LIMIT = 20
    USER_WINDOW_DAY_SECONDS = 86400

    MAX_CONCURRENT_JOBS = 2

    def __init__(self, limiter: SlidingWindowRateLimiter) -> None:
        self.limiter = limiter

    async def check_and_acquire(self, user_id: UUID, job_id: UUID) -> None:
        """Evaluate short-window, daily-window, and concurrency limits.

        Raises TryOnRateLimitExceeded if any threshold is violated.
        """
        user_str = str(user_id)
        job_str = str(job_id)

        # 1. Check concurrency
        concurrency_key = f"tryon:concurrency:user:{user_str}"
        acquired = await self.limiter.acquire_concurrency(
            key=concurrency_key,
            job_id=job_str,
            max_concurrent=self.MAX_CONCURRENT_JOBS,
        )
        if not acquired:
            raise TryOnRateLimitExceeded(
                message=f"You already have {self.MAX_CONCURRENT_JOBS} active try-on jobs. Please wait for them to finish.",
                limit_type="USER_CONCURRENCY",
                limit=self.MAX_CONCURRENT_JOBS,
                retry_after=15,
            )

        # 2. Check 10-minute sliding window
        window_10m_key = f"tryon:ratelimit:user:10m:{user_str}"
        res_10m = await self.limiter.check_rate_limit(
            key=window_10m_key,
            limit=self.USER_WINDOW_10M_LIMIT,
            window_seconds=self.USER_WINDOW_10M_SECONDS,
        )
        if not res_10m.allowed:
            # Release acquired concurrency slot
            await self.limiter.release_concurrency(concurrency_key, job_str)
            raise TryOnRateLimitExceeded(
                message="You have requested too many try-on generations recently. Please try again shortly.",
                limit_type="USER_BURST_10M",
                limit=self.USER_WINDOW_10M_LIMIT,
                retry_after=res_10m.retry_after_seconds,
            )

        # 3. Check 24-hour daily window
        window_day_key = f"tryon:ratelimit:user:day:{user_str}"
        res_day = await self.limiter.check_rate_limit(
            key=window_day_key,
            limit=self.USER_WINDOW_DAY_LIMIT,
            window_seconds=self.USER_WINDOW_DAY_SECONDS,
        )
        if not res_day.allowed:
            await self.limiter.release_concurrency(concurrency_key, job_str)
            raise TryOnRateLimitExceeded(
                message="You have reached your daily virtual try-on limit (20 generations per day).",
                limit_type="USER_DAILY_24H",
                limit=self.USER_WINDOW_DAY_LIMIT,
                retry_after=res_day.retry_after_seconds,
            )

    async def release_concurrency(self, user_id: UUID, job_id: UUID) -> None:
        """Release concurrency lease when job concludes."""
        concurrency_key = f"tryon:concurrency:user:{user_id}"
        await self.limiter.release_concurrency(concurrency_key, str(job_id))
