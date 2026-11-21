"""Distributed token-bucket rate limiter for catalog source operations."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass


@dataclass
class _BucketState:
    tokens: float
    last_updated: float
    retry_after_until: float = 0.0


class DistributedRateLimiter:
    """Token-bucket rate limiter coordinated across operations with Retry-After support."""

    def __init__(self) -> None:
        self._buckets: dict[str, _BucketState] = {}
        self._lock = asyncio.Lock()

    async def record_retry_after(self, key: str, seconds: float) -> None:
        """Enforce backoff for the specified key based on provider Retry-After header."""
        async with self._lock:
            state = self._buckets.setdefault(
                key, _BucketState(tokens=1.0, last_updated=time.time())
            )
            state.retry_after_until = max(state.retry_after_until, time.time() + seconds)
            state.tokens = 0.0

    async def acquire(self, key: str, max_rps: float) -> float:
        """Acquire permission to execute a request for key. Sleeps if throttled."""
        if max_rps <= 0:
            return 0.0

        async with self._lock:
            now = time.time()
            state = self._buckets.setdefault(
                key, _BucketState(tokens=float(max_rps), last_updated=now)
            )

            # Check if currently locked under Retry-After
            if state.retry_after_until > now:
                wait_time = state.retry_after_until - now
                await asyncio.sleep(wait_time)
                now = time.time()

            # Replenish tokens based on elapsed time
            elapsed = now - state.last_updated
            state.tokens = min(float(max_rps), state.tokens + (elapsed * max_rps))
            state.last_updated = now

            if state.tokens >= 1.0:
                state.tokens -= 1.0
                return 0.0

            # Calculate wait time until 1 token is available
            needed = 1.0 - state.tokens
            wait_time = needed / max_rps
            state.tokens = 0.0
            state.last_updated = now + wait_time

        await asyncio.sleep(wait_time)
        return wait_time
