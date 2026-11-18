"""Bounded exponential backoff retry helper with jitter and provider error handling."""

from __future__ import annotations

import asyncio
import logging
import random
from collections.abc import Callable
from typing import Any, TypeVar

import httpx

from fashx.catalog.acquisition.auth import SourceAuthProvider

logger = logging.getLogger(__name__)

T = TypeVar("T")

RETRYABLE_EXCEPTIONS = (
    TimeoutError,
    ConnectionError,
    asyncio.TimeoutError,
    OSError,
    httpx.TimeoutException,
    httpx.NetworkError,
)


async def retry_transient(
    operation: Callable[[], Any],
    *,
    max_attempts: int = 4,
    base_delay_seconds: float = 0.5,
    retryable_exceptions: tuple[type[Exception], ...] = RETRYABLE_EXCEPTIONS,
) -> Any:
    """Execute operation with bounded exponential backoff and randomized jitter."""
    for attempt in range(max_attempts):
        try:
            res = operation()
            if asyncio.iscoroutine(res):
                return await res
            return res
        except retryable_exceptions:
            if attempt == max_attempts - 1:
                raise
            delay = base_delay_seconds * (2**attempt)
            jitter = random.uniform(0, delay * 0.2)
            await asyncio.sleep(delay + jitter)


class SourceRetryPolicy:
    """Production retry policy enforcing bounds on transient errors and single-retry on 401."""

    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay_seconds: float = 1.0,
        max_delay_seconds: float = 30.0,
        multiplier: float = 2.0,
    ) -> None:
        self.max_attempts = max_attempts
        self.initial_delay_seconds = initial_delay_seconds
        self.max_delay_seconds = max_delay_seconds
        self.multiplier = multiplier

    async def execute(
        self,
        fn: Callable[[], Any],
        source_id: str = "",
        auth_provider: SourceAuthProvider | None = None,
    ) -> Any:
        attempt = 0
        auth_refreshed = False

        while attempt < self.max_attempts:
            attempt += 1
            try:
                res = fn()
                if asyncio.iscoroutine(res):
                    return await res
                return res
            except httpx.HTTPStatusError as exc:
                status = exc.response.status_code

                # 401: Refresh credentials once and retry
                if status == 401 and not auth_refreshed and auth_provider:
                    auth_refreshed = True
                    await auth_provider.invalidate(source_id)
                    continue

                # 400, 403, 404, or repeated 401: Non-retryable
                if status in (400, 403, 404) or (status == 401 and auth_refreshed):
                    raise

                # 429: Respect Retry-After header
                if status == 429:
                    retry_after = exc.response.headers.get("retry-after")
                    wait_sec = float(retry_after) if retry_after and retry_after.isdigit() else 2.0
                    if attempt >= self.max_attempts:
                        raise
                    await asyncio.sleep(min(wait_sec, self.max_delay_seconds))
                    continue

                # 5xx: Transient error retry
                if status in (500, 502, 503, 504):
                    if attempt >= self.max_attempts:
                        raise
                    delay = min(
                        self.max_delay_seconds,
                        self.initial_delay_seconds * (self.multiplier ** (attempt - 1)),
                    )
                    jitter = random.uniform(0, delay * 0.2)
                    await asyncio.sleep(delay + jitter)
                    continue

                raise

            except RETRYABLE_EXCEPTIONS:
                if attempt >= self.max_attempts:
                    raise
                delay = min(
                    self.max_delay_seconds,
                    self.initial_delay_seconds * (self.multiplier ** (attempt - 1)),
                )
                jitter = random.uniform(0, delay * 0.2)
                await asyncio.sleep(delay + jitter)
