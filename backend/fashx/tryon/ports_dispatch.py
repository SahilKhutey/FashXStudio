from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Protocol
from uuid import UUID

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DispatchResult:
    accepted: bool
    reason: str | None = None


class TryOnJobDispatcher(Protocol):
    async def dispatch(self, job_id: UUID) -> DispatchResult | None:
        """Schedule a persisted try-on job for asynchronous processing."""
        ...


class CeleryTryOnJobDispatcher:
    """Dispatches try-on job to Celery worker queue with observable result."""

    async def dispatch(self, job_id: UUID) -> DispatchResult:
        try:
            from fashx.workers.app import process_tryon_job

            process_tryon_job.apply_async(
                args=[str(job_id)],
                retry=False,
                retry_policy={"max_retries": 0},
                ignore_result=True,
            )
            logger.info("Dispatched try-on job %s to Celery queue", job_id)
            return DispatchResult(accepted=True)
        except Exception as exc:
            logger.warning("Direct Celery dispatch for job %s deferred: %s", job_id, exc)
            return DispatchResult(accepted=False, reason=type(exc).__name__)


class DirectTryOnJobDispatcher:
    """In-process dispatcher for testing and development."""

    def __init__(self, use_case_factory: Any | None = None) -> None:
        self.use_case_factory = use_case_factory

    async def dispatch(self, job_id: UUID) -> DispatchResult:
        if self.use_case_factory:
            if callable(self.use_case_factory) and not hasattr(self.use_case_factory, "execute"):
                use_case = self.use_case_factory()
            else:
                use_case = self.use_case_factory
            await use_case.execute(job_id)
        return DispatchResult(accepted=True)
