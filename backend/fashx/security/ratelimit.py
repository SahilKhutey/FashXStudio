import logging
import time
from collections import defaultdict
from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

from fastapi import Depends, Request, Response

from fashx.core.settings import get_settings

from .deps import Principal, get_optional_principal
from .errors import too_many_requests

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RateLimitResult:
    allowed: bool
    limit: int
    remaining: int
    reset_seconds: int


class RateLimiter:
    """Interface for rate limiting backends."""

    async def check(
        self, key: str, max_requests: int, window_seconds: int
    ) -> RateLimitResult: ...


class InMemoryRateLimiter(RateLimiter):
    """In-memory sliding-window counter for development, test, and fallback."""

    def __init__(self) -> None:
        self._requests: dict[str, list[float]] = defaultdict(list)

    async def check(
        self, key: str, max_requests: int, window_seconds: int
    ) -> RateLimitResult:
        now = time.time()
        window_start = now - window_seconds
        # Clean older requests outside current window
        history = [ts for ts in self._requests[key] if ts > window_start]
        self._requests[key] = history

        remaining = max_requests - len(history)
        if remaining <= 0:
            oldest = history[0] if history else now
            reset_seconds = max(1, int(oldest + window_seconds - now))
            return RateLimitResult(
                allowed=False,
                limit=max_requests,
                remaining=0,
                reset_seconds=reset_seconds,
            )

        history.append(now)
        reset_seconds = window_seconds
        return RateLimitResult(
            allowed=True,
            limit=max_requests,
            remaining=remaining - 1,
            reset_seconds=reset_seconds,
        )


class RedisRateLimiter(RateLimiter):
    """Redis-backed rate limiter with sliding window / atomic expiration."""

    def __init__(self, redis_url: str) -> None:
        self._redis_url = redis_url
        self._client: Any = None
        self._fallback = InMemoryRateLimiter()

    async def _get_client(self) -> Any:
        if self._client is None:
            try:
                import redis.asyncio as aioredis

                self._client = aioredis.from_url(
                    self._redis_url,
                    decode_responses=True,
                    socket_connect_timeout=2.0,
                )
            except Exception as e:
                logger.warning(f"Failed to connect to Redis for rate limiting: {e}")
                return None
        return self._client

    async def check(
        self, key: str, max_requests: int, window_seconds: int
    ) -> RateLimitResult:
        client = await self._get_client()
        if client is None:
            return await self._fallback.check(key, max_requests, window_seconds)

        try:
            pipe = client.pipeline()
            pipe.incr(key)
            pipe.ttl(key)
            results = await pipe.execute()
            count, ttl = results[0], results[1]

            if count == 1 or ttl == -1:
                await client.expire(key, window_seconds)
                ttl = window_seconds

            reset_seconds = max(1, ttl)
            remaining = max(0, max_requests - count)
            allowed = count <= max_requests

            return RateLimitResult(
                allowed=allowed,
                limit=max_requests,
                remaining=remaining,
                reset_seconds=reset_seconds,
            )
        except Exception as e:
            logger.warning(f"Redis rate limit check error, falling back to memory: {e}")
            return await self._fallback.check(key, max_requests, window_seconds)


@lru_cache(maxsize=1)
def get_rate_limiter() -> RateLimiter:
    settings = get_settings()
    if settings.env == "test":
        return InMemoryRateLimiter()
    return RedisRateLimiter(settings.redis_url)


def rate_limit(
    max_requests: int = 60,
    window_seconds: int = 60,
    scope: str = "default",
) -> Callable[[Request, Response, Principal | None], Coroutine[Any, Any, None]]:
    """FastAPI dependency factory enforcing rate limits on endpoints."""

    async def _dependency(
        request: Request,
        response: Response,
        principal: Principal | None = Depends(get_optional_principal),
    ) -> None:
        identifier = (
            principal.user_id
            if principal
            else (request.client.host if request.client else "unknown")
        )
        key = f"fashx:ratelimit:{scope}:{identifier}"
        limiter = get_rate_limiter()
        result = await limiter.check(key, max_requests, window_seconds)

        response.headers["X-RateLimit-Limit"] = str(result.limit)
        response.headers["X-RateLimit-Remaining"] = str(result.remaining)
        response.headers["X-RateLimit-Reset"] = str(result.reset_seconds)

        if not result.allowed:
            raise too_many_requests(retry_after=result.reset_seconds)

    return _dependency
