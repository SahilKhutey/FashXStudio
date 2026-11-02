from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from uuid import UUID, uuid4

from fashx.tryon.application.process_job import ProcessJobResult, ProcessTryOnJobUseCase
from fashx.tryon.repositories.tryon_repository import TryOnUnitOfWork

log = logging.getLogger(__name__)


class TryOnWorker:
    """Asynchronous polling worker that claims queued try-on jobs and coordinates inference.

    Transactions:
    1. Short, dedicated transaction to claim the job and commit immediately.
    2. Inference, image downloading, and watermarking run OUTSIDE database transactions.
    3. Dedicated transaction for status updates, lease renewal, or completion.
    """

    def __init__(
        self,
        uow_factory: Callable[[], TryOnUnitOfWork],
        process_job_factory: Callable[[], ProcessTryOnJobUseCase],
        *,
        worker_id: str | None = None,
        lease_seconds: int = 180,
        poll_seconds: float = 2.0,
    ) -> None:
        self.uow_factory = uow_factory
        self.process_job_factory = process_job_factory
        self.worker_id = worker_id or f"tryon-{uuid4()}"
        self.lease_seconds = lease_seconds
        self.poll_seconds = poll_seconds
        self._running = False
        self._current_job_id: UUID | None = None

    async def claim_job(self) -> UUID | None:
        """Atomically claims the next eligible job inside a short transaction."""
        async with self.uow_factory() as uow:
            job = await uow.jobs.claim_next_job(
                self.worker_id, lease_seconds=self.lease_seconds
            )
            if job is None:
                return None
            job_id = job.id
            await uow.commit()
            return job_id

    async def renew_current_lease(self, job_id: UUID) -> bool:
        """Heartbeat to renew the active worker lease."""
        try:
            async with self.uow_factory() as uow:
                renewed = await uow.jobs.renew_lease(
                    job_id, self.worker_id, lease_seconds=self.lease_seconds
                )
                await uow.commit()
                return renewed
        except Exception as exc:
            log.warning("Failed to renew lease for job %s: %s", job_id, exc)
            return False

    async def release_current_lease(self, job_id: UUID) -> bool:
        """Releases the worker lease upon graceful shutdown or failure."""
        try:
            async with self.uow_factory() as uow:
                released = await uow.jobs.release_lease(job_id, self.worker_id)
                await uow.commit()
                return released
        except Exception as exc:
            log.warning("Failed to release lease for job %s: %s", job_id, exc)
            return False

    async def process_job(self, job_id: UUID) -> ProcessJobResult:
        """Executes the try-on process outside the transaction with lease renewal."""
        self._current_job_id = job_id
        process_uc = self.process_job_factory()

        async def heartbeat() -> None:
            interval = max(5.0, self.lease_seconds / 3.0)
            while True:
                await asyncio.sleep(interval)
                if not await self.renew_current_lease(job_id):
                    break

        heartbeat_task = asyncio.create_task(heartbeat())
        try:
            result = await process_uc.execute(job_id)
            return result
        finally:
            heartbeat_task.cancel()
            try:
                await heartbeat_task
            except asyncio.CancelledError:
                pass
            self._current_job_id = None

    async def process_one(self) -> ProcessJobResult | None:
        """Polls for and executes one job, returning None if no job was available."""
        job_id = await self.claim_job()
        if job_id is None:
            return None
        return await self.process_job(job_id)

    async def run_loop(self, max_jobs: int | None = None) -> int:
        """Runs the worker polling loop until stopped or max_jobs is reached."""
        self._running = True
        jobs_processed = 0

        while self._running:
            try:
                result = await self.process_one()
                if result is not None:
                    jobs_processed += 1
                    if max_jobs is not None and jobs_processed >= max_jobs:
                        break
                else:
                    await asyncio.sleep(self.poll_seconds)
            except Exception as exc:
                log.exception("Unexpected error in worker loop: %s", exc)
                await asyncio.sleep(self.poll_seconds)

        return jobs_processed

    def stop(self) -> None:
        """Signals the worker to finish its active job and stop polling."""
        self._running = False
