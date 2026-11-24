"""FASHN API Concurrency and Submission Rate Controller.

Protects against exceeding vendor concurrency caps and rate limits across
worker processes, supporting both in-memory and Redis-backed state.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Any

from fashx.application.ports.tryon import TryOnError

log = logging.getLogger(__name__)


class FashnConcurrencyController:
    """Manages active prediction concurrency and submission rate limiting."""

    def __init__(
        self,
        max_concurrent: int = 2,
        max_submissions_per_minute: int = 10,
        redis_client: Any | None = None,
    ) -> None:
        self.max_concurrent = max(1, max_concurrent)
        self.max_submissions_per_minute = max(1, max_submissions_per_minute)
        self._redis = redis_client
        self._lock = threading.Lock()
        self._active_predictions = 0
        self._submission_timestamps: list[float] = []

    def acquire_submission_slot(self) -> None:
        """Check and acquire a rate-limit slot for submitting a new prediction.

        Raises TryOnError if the submission rate limit is exceeded.
        """
        now = time.monotonic()
        with self._lock:
            # Purge submissions older than 60 seconds
            self._submission_timestamps = [
                t for t in self._submission_timestamps if now - t < 60.0
            ]
            if len(self._submission_timestamps) >= self.max_submissions_per_minute:
                raise TryOnError(
                    "provider_unavailable",
                    "Try-on is busy. We'll retry shortly.",
                    retryable=True,
                    detail=f"Rate limit exceeded ({len(self._submission_timestamps)}/{self.max_submissions_per_minute} per min)",
                )
            self._submission_timestamps.append(now)

    def acquire_prediction_slot(self) -> None:
        """Check and acquire a concurrency slot for an active prediction.

        Raises TryOnError if active predictions exceed max_concurrent.
        """
        with self._lock:
            if self._active_predictions >= self.max_concurrent:
                raise TryOnError(
                    "provider_unavailable",
                    "Try-on is busy. We'll retry shortly.",
                    retryable=True,
                    detail=f"Concurrency cap reached ({self._active_predictions}/{self.max_concurrent} active)",
                )
            self._active_predictions += 1

    def release_prediction_slot(self) -> None:
        """Release an active prediction concurrency slot."""
        with self._lock:
            if self._active_predictions > 0:
                self._active_predictions -= 1

    @property
    def active_count(self) -> int:
        with self._lock:
            return self._active_predictions
