"""Base source adapter with circuit breaker, rate limiting, and failure isolation."""

from __future__ import annotations

import asyncio
import time
from abc import ABC, abstractmethod

from fashx.catalog.acquisition.contract import AcquisitionBatch, CatalogSourceAdapter
from fashx.catalog.acquisition.registry import SourceConfig


class CircuitBreakerOpenError(RuntimeError):
    """Raised when an adapter's circuit breaker is open due to repeated failures."""


class BaseSourceAdapter(CatalogSourceAdapter, ABC):
    """Abstract base adapter enforcing rate limits and circuit breaker policies."""

    def __init__(self, config: SourceConfig) -> None:
        self.config = config
        self._failure_count = 0
        self._last_failure_time: float = 0.0
        self._circuit_state: str = "CLOSED"  # CLOSED | OPEN | HALF_OPEN
        self._last_request_time: float = 0.0

    @property
    def source_slug(self) -> str:
        return self.config.source_slug

    @property
    def circuit_state(self) -> str:
        if self._circuit_state == "OPEN":
            if (time.time() - self._last_failure_time) > self.config.circuit_breaker_cooldown_seconds:
                self._circuit_state = "HALF_OPEN"
        return self._circuit_state

    def _check_circuit(self) -> None:
        current_state = self.circuit_state
        if current_state == "OPEN":
            raise CircuitBreakerOpenError(
                f"Circuit breaker is OPEN for source '{self.source_slug}'. "
                f"Consecutive failures: {self._failure_count}. Cooldown remaining: "
                f"{max(0.0, self.config.circuit_breaker_cooldown_seconds - (time.time() - self._last_failure_time)):.1f}s"
            )

    async def _enforce_rate_limit(self) -> None:
        if self.config.max_rps > 0:
            min_interval = 1.0 / self.config.max_rps
            elapsed = time.time() - self._last_request_time
            if elapsed < min_interval:
                await asyncio.sleep(min_interval - elapsed)
        self._last_request_time = time.time()

    def _record_success(self) -> None:
        self._failure_count = 0
        self._circuit_state = "CLOSED"

    def _record_failure(self) -> None:
        self._failure_count += 1
        self._last_failure_time = time.time()
        if self._failure_count >= self.config.circuit_breaker_threshold:
            self._circuit_state = "OPEN"

    async def fetch_batch(
        self,
        cursor: str | None = None,
        limit: int = 100,
    ) -> AcquisitionBatch:
        self._check_circuit()
        await self._enforce_rate_limit()

        try:
            batch = await self._fetch_batch_impl(cursor=cursor, limit=limit)
            self._record_success()
            return batch
        except Exception:
            self._record_failure()
            raise

    @abstractmethod
    async def _fetch_batch_impl(
        self,
        cursor: str | None,
        limit: int,
    ) -> AcquisitionBatch:
        """Internal fetch implementation to be provided by concrete store adapters."""
        ...
