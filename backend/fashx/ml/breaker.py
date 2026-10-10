"""Circuit breaker and budget protection for try-on operations."""

import time
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.tryon import TryOnJob, TryOnUsage
from fashx.application.ports.tryon import TryOnError


class Breaker:
    """Redis or in-memory backed circuit breaker for provider call protection."""

    def __init__(
        self,
        r: Any,
        name: str = "tryon",
        threshold: int = 5,
        window_s: int = 60,
        open_s: int = 60,
    ) -> None:
        self.r = r
        self.k = f"cb:{name}"
        self.th = threshold
        self.w = window_s
        self.o = open_s

    def guard(self) -> None:
        """Check if circuit is open and raise retryable breaker_open."""
        if hasattr(self.r, "exists") and self.r.exists(self.k + ":open"):
            raise TryOnError(
                "breaker_open",
                "Try-on is busy. We'll retry shortly.",
                retryable=True,
                detail="circuit open",
            )

    def failure(self) -> None:
        """Record vendor trouble failure and potentially trip the breaker."""
        if hasattr(self.r, "incr"):
            n = self.r.incr(self.k + ":fails")
            self.r.expire(self.k + ":fails", self.w)
            if n >= self.th:
                self.r.set(self.k + ":open", 1, ex=self.o)

    def success(self) -> None:
        """Reset consecutive failures on successful execution."""
        if hasattr(self.r, "delete"):
            self.r.delete(self.k + ":fails")


class InMemoryBreaker:
    """Self-contained in-memory circuit breaker for tests and single-node development."""

    def __init__(
        self,
        threshold: int = 5,
        window_s: int = 60,
        open_s: int = 60,
    ) -> None:
        self.threshold = threshold
        self.window_s = window_s
        self.open_s = open_s
        self.failures = 0
        self.first_failure_time = 0.0
        self.opened_until = 0.0

    def guard(self) -> None:
        now = time.monotonic()
        if now < self.opened_until:
            raise TryOnError(
                "breaker_open",
                "Try-on is busy. We'll retry shortly.",
                retryable=True,
                detail="circuit open",
            )

    def failure(self) -> None:
        now = time.monotonic()
        if now - self.first_failure_time > self.window_s:
            self.failures = 1
            self.first_failure_time = now
        else:
            self.failures += 1

        if self.failures >= self.threshold:
            self.opened_until = now + self.open_s

    def success(self) -> None:
        self.failures = 0
        self.first_failure_time = 0.0


async def check_daily_budget_exceeded(session: AsyncSession, budget_limit_usd: float) -> bool:
    """Check if total estimated tryon_usage cost today exceeds daily budget limit."""
    from datetime import UTC, datetime

    start_of_day = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    stmt = select(func.coalesce(func.sum(TryOnUsage.cost_usd_est), 0)).where(
        TryOnUsage.created_at >= start_of_day
    )
    result = await session.scalar(stmt)
    total_spent = float(result or 0.0)
    return total_spent >= budget_limit_usd


async def check_user_daily_cap_exceeded(session: AsyncSession, user_id: UUID, daily_cap: int) -> bool:
    """Check if user has reached their daily allowed try-on job quota."""
    from datetime import UTC, datetime

    start_of_day = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    stmt = select(func.count()).select_from(TryOnJob).where(
        TryOnJob.user_id == user_id,
        TryOnJob.created_at >= start_of_day,
    )
    result = await session.scalar(stmt)
    count = int(result or 0)
    return count >= daily_cap
