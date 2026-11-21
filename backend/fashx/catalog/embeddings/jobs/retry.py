from __future__ import annotations

import logging
import random
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.orm import Session

from database.models.catalog_embeddings import EmbeddingJobRecord
from fashx.catalog.embeddings.preprocessing import PreprocessingError
from fashx.catalog.embeddings.service import EmbeddingPermissionDeniedError

logger = logging.getLogger(__name__)


class EmbeddingRetryPolicy:
    """Calculates exponential backoff delay with jitter."""

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 30.0,
        jitter: float = 0.5,
    ) -> None:
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.jitter = jitter

    def compute_backoff(self, attempt: int) -> float:
        """Compute delay in seconds for given retry attempt."""
        delay = min(self.max_delay, self.base_delay * (2 ** (attempt - 1)))
        delay += random.uniform(0, self.jitter)
        return round(delay, 3)

    def is_retryable(self, exc: Exception, attempt: int) -> bool:
        """Determine whether an error is transient and eligible for retry."""
        if attempt >= self.max_retries:
            return False

        # Permanent fatal errors
        if isinstance(exc, (ValueError, PreprocessingError, EmbeddingPermissionDeniedError)):
            return False

        # Transient network / timeout errors
        if isinstance(exc, (TimeoutError, ConnectionError, OSError)):
            return True

        # Generic runtime errors retry up to limit
        return True


class EmbeddingRetryHandler:
    """Manages failure handling, backoff scheduling, and dead-letter queuing."""

    def __init__(self, policy: EmbeddingRetryPolicy | None = None) -> None:
        self.policy = policy or EmbeddingRetryPolicy()

    def handle_failure(
        self,
        session: Session,
        job_id: UUID,
        exc: Exception,
    ) -> EmbeddingJobRecord:
        """Record error details and update job state according to retry policy."""
        job = session.get(EmbeddingJobRecord, job_id)
        if job is None:
            raise KeyError(f"Embedding job {job_id} not found")

        job.attempts += 1
        job.last_error = f"{type(exc).__name__}: {str(exc)}"

        if self.policy.is_retryable(exc, job.attempts):
            job.status = "RETRY_QUEUED"
            logger.warning(
                "Job %s failed attempt %d, queued for retry: %s",
                job_id,
                job.attempts,
                exc,
            )
        else:
            job.status = "FAILED"
            job.completed_at = datetime.now(UTC)
            logger.error(
                "Job %s permanently failed after %d attempts (DLQ): %s",
                job_id,
                job.attempts,
                exc,
            )

        session.flush()
        return job


__all__ = [
    "EmbeddingRetryHandler",
    "EmbeddingRetryPolicy",
]
