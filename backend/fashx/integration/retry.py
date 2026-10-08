from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import TypeVar

T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    max_attempts: int = 3
    base_delay_seconds: float = 0.1
    max_delay_seconds: float = 5.0

    async def execute(
        self,
        operation: Callable[[], Awaitable[T]],
    ) -> T:
        attempt = 0

        while True:
            attempt += 1

            try:
                return await operation()
            except Exception:
                if attempt >= self.max_attempts:
                    raise

                delay = min(
                    self.max_delay_seconds,
                    self.base_delay_seconds * (2 ** (attempt - 1)),
                )

                if delay > 0:
                    await asyncio.sleep(delay)
