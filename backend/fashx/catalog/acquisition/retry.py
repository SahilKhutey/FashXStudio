"""Bounded exponential backoff retry helper with jitter for transient operations."""

from __future__ import annotations

import asyncio
import random
from collections.abc import Callable
from typing import Any, TypeVar

T = TypeVar("T")

RETRYABLE_EXCEPTIONS = (
    TimeoutError,
    ConnectionError,
    asyncio.TimeoutError,
    OSError,
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
