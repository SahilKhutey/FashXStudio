"""Distributed sliding window rate limiter and concurrency controller.

Uses Redis sorted sets (ZSET) with Lua scripts for atomic sliding window evaluation.
Provides an automatic in-memory fallback when Redis is unavailable (e.g. unit tests).
"""

from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)

# Redis Lua script for atomic sliding window rate limiting
SLIDING_WINDOW_LUA = """
local key = KEYS[1]
local now = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local limit = tonumber(ARGV[3])
local member_id = ARGV[4]

local clear_before = now - window
redis.call('ZREMRANGEBYSCORE', key, 0, clear_before)

local current_count = redis.call('ZCARD', key)
if current_count < limit then
    redis.call('ZADD', key, now, member_id)
    redis.call('EXPIRE', key, window + 10)
    local remaining = limit - current_count - 1
    return {1, remaining, 0}
else
    local oldest = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')
    local retry_after = 1
    if #oldest > 1 then
        retry_after = math.ceil(tonumber(oldest[2]) + window - now)
        if retry_after < 1 then retry_after = 1 end
    end
    return {0, 0, retry_after}
end
"""


@dataclass
class RateLimitResult:
    """Outcome of a rate limit check."""

    allowed: bool
    limit: int
    remaining: int
    retry_after_seconds: int
    reset_seconds: int


class SlidingWindowRateLimiter:
    """High-performance sliding window rate limiter."""

    def __init__(self, redis_client: Any | None = None) -> None:
        self.redis = redis_client
        # In-memory storage for test/fallback: key -> list of (timestamp, member_id)
        self._memory_store: dict[str, list[tuple[float, str]]] = {}
        # Concurrency in-memory storage: key -> set of job_ids
        self._memory_concurrency: dict[str, set[str]] = {}

    async def check_rate_limit(
        self,
        key: str,
        limit: int,
        window_seconds: int,
    ) -> RateLimitResult:
        """Check if request is permitted within the sliding window."""
        now = time.time()
        member_id = f"{now}:{uuid.uuid4().hex[:8]}"

        if self.redis is not None:
            try:
                res = await self.redis.eval(
                    SLIDING_WINDOW_LUA,
                    1,
                    key,
                    str(now),
                    str(window_seconds),
                    str(limit),
                    member_id,
                )
                allowed = bool(res[0])
                remaining = int(res[1])
                retry_after = int(res[2])
                return RateLimitResult(
                    allowed=allowed,
                    limit=limit,
                    remaining=remaining,
                    retry_after_seconds=retry_after,
                    reset_seconds=window_seconds,
                )
            except Exception as e:
                logger.warning("Redis rate limiter failed (%s); falling back to memory", e)

        # In-memory sliding window implementation
        timestamps = self._memory_store.setdefault(key, [])
        threshold = now - window_seconds
        # Remove expired timestamps
        timestamps[:] = [item for item in timestamps if item[0] > threshold]

        if len(timestamps) < limit:
            timestamps.append((now, member_id))
            remaining = limit - len(timestamps)
            return RateLimitResult(
                allowed=True,
                limit=limit,
                remaining=remaining,
                retry_after_seconds=0,
                reset_seconds=window_seconds,
            )
        else:
            oldest_ts = timestamps[0][0]
            retry_after = max(1, int(oldest_ts + window_seconds - now + 0.999))
            return RateLimitResult(
                allowed=False,
                limit=limit,
                remaining=0,
                retry_after_seconds=retry_after,
                reset_seconds=window_seconds,
            )

    async def acquire_concurrency(
        self,
        key: str,
        job_id: str,
        max_concurrent: int,
        ttl_seconds: int = 300,
    ) -> bool:
        """Attempt to acquire a concurrency slot for an in-flight job."""
        if self.redis is not None:
            try:
                current_count = await self.redis.scard(key)
                if current_count >= max_concurrent:
                    return False
                await self.redis.sadd(key, job_id)
                await self.redis.expire(key, ttl_seconds)
                return True
            except Exception as e:
                logger.warning("Redis concurrency check failed (%s); falling back to memory", e)

        active_jobs = self._memory_concurrency.setdefault(key, set())
        if len(active_jobs) >= max_concurrent:
            return False
        active_jobs.add(job_id)
        return True

    async def release_concurrency(self, key: str, job_id: str) -> None:
        """Release a concurrency slot upon job completion or termination."""
        if self.redis is not None:
            try:
                await self.redis.srem(key, job_id)
                return
            except Exception as e:
                logger.warning("Redis concurrency release failed (%s); releasing memory", e)

        active_jobs = self._memory_concurrency.get(key)
        if active_jobs and job_id in active_jobs:
            active_jobs.remove(job_id)
