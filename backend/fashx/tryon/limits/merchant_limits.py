"""Merchant rate limiting and concurrency enforcement.

Rules:
1. Short-term window: 60 requests per minute.
2. Concurrency limit: Maximum 20 concurrent in-flight jobs across the merchant's catalog.
"""

from __future__ import annotations

from uuid import UUID

from backend.fashx.tryon.limits.redis_limiter import SlidingWindowRateLimiter
from backend.fashx.tryon.limits.user_limits import TryOnRateLimitExceeded


class MerchantRateLimiter:
    """Enforces merchant-tier rate and concurrency limits."""

    MERCHANT_WINDOW_1M_LIMIT = 60
    MERCHANT_WINDOW_1M_SECONDS = 60

    MAX_CONCURRENT_JOBS = 20

    def __init__(self, limiter: SlidingWindowRateLimiter) -> None:
        self.limiter = limiter

    async def check_and_acquire(self, merchant_id: UUID | str, job_id: UUID) -> None:
        """Evaluate per-minute and concurrency limits for a merchant.

        Raises TryOnRateLimitExceeded if thresholds are breached.
        """
        merchant_str = str(merchant_id)
        job_str = str(job_id)

        # 1. Check concurrency
        concurrency_key = f"tryon:concurrency:merchant:{merchant_str}"
        acquired = await self.limiter.acquire_concurrency(
            key=concurrency_key,
            job_id=job_str,
            max_concurrent=self.MAX_CONCURRENT_JOBS,
        )
        if not acquired:
            raise TryOnRateLimitExceeded(
                message=f"Merchant concurrency ceiling reached ({self.MAX_CONCURRENT_JOBS} active jobs). Please retry in a few seconds.",
                limit_type="MERCHANT_CONCURRENCY",
                limit=self.MAX_CONCURRENT_JOBS,
                retry_after=10,
            )

        # 2. Check 1-minute window
        window_1m_key = f"tryon:ratelimit:merchant:1m:{merchant_str}"
        res_1m = await self.limiter.check_rate_limit(
            key=window_1m_key,
            limit=self.MERCHANT_WINDOW_1M_LIMIT,
            window_seconds=self.MERCHANT_WINDOW_1M_SECONDS,
        )
        if not res_1m.allowed:
            await self.limiter.release_concurrency(concurrency_key, job_str)
            raise TryOnRateLimitExceeded(
                message="Merchant API rate limit exceeded (60 requests/min). Please throttle requests.",
                limit_type="MERCHANT_BURST_1M",
                limit=self.MERCHANT_WINDOW_1M_LIMIT,
                retry_after=res_1m.retry_after_seconds,
            )

    async def release_concurrency(self, merchant_id: UUID | str, job_id: UUID) -> None:
        """Release concurrency lease for the merchant."""
        concurrency_key = f"tryon:concurrency:merchant:{merchant_id}"
        await self.limiter.release_concurrency(concurrency_key, str(job_id))
