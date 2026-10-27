from __future__ import annotations

import logging
from typing import Any, Protocol
from uuid import UUID

logger = logging.getLogger(__name__)


class TryOnJobDispatcher(Protocol):
    async def dispatch(self, job_id: UUID) -> None:
        """Schedule a persisted try-on job for asynchronous processing."""
        ...


class CeleryTryOnJobDispatcher:
    """Dispatches try-on job to Celery worker queue."""

    async def dispatch(self, job_id: UUID) -> None:
        try:
            from fashx.workers.app import process_tryon_job

            process_tryon_job.delay(str(job_id))
            logger.info("Dispatched try-on job %s to Celery queue", job_id)
        except Exception as exc:
            logger.warning("Direct Celery dispatch for job %s deferred: %s", job_id, exc)


class DirectTryOnJobDispatcher:
    """In-process dispatcher for testing and development."""

    def __init__(self, use_case_factory: Any | None = None) -> None:
        self.use_case_factory = use_case_factory

    async def dispatch(self, job_id: UUID) -> None:
        if self.use_case_factory:
            if callable(self.use_case_factory) and not hasattr(self.use_case_factory, "execute"):
                use_case = self.use_case_factory()
            else:
                use_case = self.use_case_factory
            await use_case.execute(job_id)
