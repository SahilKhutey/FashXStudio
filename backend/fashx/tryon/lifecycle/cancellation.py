"""VTO Job Cancellation Workflow, State Progression, and Race Protection (Phase 07.5)."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from fashx.tryon.lifecycle.states import JobStatus, normalize_job_status
from fashx.tryon.lifecycle.transitions import validate_transition

log = logging.getLogger(__name__)


class JobNotFoundError(Exception):
    """Raised when job does not exist or does not belong to requesting principal (anti-enumeration)."""

    def __init__(self, job_id: UUID) -> None:
        self.job_id = job_id
        super().__init__(f"Job {job_id} not found")


class CancellationConflictError(Exception):
    """Raised when cancellation cannot proceed due to terminal completed state."""

    def __init__(self, job_id: UUID, current_status: JobStatus) -> None:
        self.job_id = job_id
        self.current_status = current_status
        super().__init__(f"Cannot cancel job {job_id} in terminal status {current_status.value}")


@dataclass(frozen=True)
class CancellationResult:
    job_id: UUID
    previous_status: JobStatus
    new_status: JobStatus
    is_immediate: bool
    user_message: str


class JobCancellationService:
    """Manages secure, owner-scoped virtual try-on cancellation requests."""

    def __init__(self, repository: Any, provider_adapter: Any | None = None) -> None:
        self.repository = repository
        self.provider_adapter = provider_adapter

    async def request_cancellation(
        self,
        *,
        job_id: UUID,
        owner_id: UUID,
        reason: str = "Shopper requested cancellation",
        now: datetime | None = None,
    ) -> CancellationResult:
        now_ts = now or datetime.now(UTC)
        job = await self.repository.get_owned(job_id=job_id, user_id=owner_id)
        if job is None:
            # Strictly 404 / anti-enumeration: do not reveal existence to foreign users
            raise JobNotFoundError(job_id)

        curr_status = normalize_job_status(job.status)

        # Idempotent return if already cancelled
        if curr_status == JobStatus.CANCELLED:
            return CancellationResult(
                job_id=job_id,
                previous_status=curr_status,
                new_status=JobStatus.CANCELLED,
                is_immediate=True,
                user_message="Your try-on has already been cancelled.",
            )

        # Completed jobs cannot be rewritten to CANCELLED (terminal immutable)
        if curr_status == JobStatus.COMPLETED:
            raise CancellationConflictError(job_id, curr_status)

        if curr_status == JobStatus.FAILED or curr_status == JobStatus.EXPIRED:
            raise CancellationConflictError(job_id, curr_status)

        # Already requested
        if curr_status == JobStatus.CANCEL_REQUESTED:
            return CancellationResult(
                job_id=job_id,
                previous_status=curr_status,
                new_status=JobStatus.CANCEL_REQUESTED,
                is_immediate=False,
                user_message="Your cancellation request has been received and is being processed.",
            )

        # States where cancellation is immediate and safe
        immediate_cancel_states = {
            JobStatus.CREATED,
            JobStatus.VALIDATING,
            JobStatus.QUEUED,
            JobStatus.RETRY_PENDING,
        }

        if curr_status in immediate_cancel_states:
            target_status = JobStatus.CANCELLED
            validate_transition(curr_status, target_status)

            await self.repository.update_status_and_event(
                job_id=job_id,
                expected_status=curr_status.value,
                new_status=target_status.value,
                actor_type="USER",
                actor_id=str(owner_id),
                reason_code="USER_CANCELLED",
                metadata={"reason": reason, "cancelled_at": now_ts.isoformat()},
                now=now_ts,
            )

            return CancellationResult(
                job_id=job_id,
                previous_status=curr_status,
                new_status=target_status,
                is_immediate=True,
                user_message="Your try-on request has been cancelled.",
            )

        # In-flight active execution (PROCESSING, SUBMISSION_UNKNOWN, OUTPUT_VALIDATING, STORING_RESULT)
        target_status = JobStatus.CANCEL_REQUESTED
        validate_transition(curr_status, target_status)

        await self.repository.update_status_and_event(
            job_id=job_id,
            expected_status=curr_status.value,
            new_status=target_status.value,
            actor_type="USER",
            actor_id=str(owner_id),
            reason_code="CANCELLATION_REQUESTED",
            metadata={"reason": reason, "requested_at": now_ts.isoformat()},
            now=now_ts,
        )

        # Attempt provider cancellation if provider adapter supports it
        if self.provider_adapter and hasattr(self.provider_adapter, "cancel") and getattr(job, "provider_job_id", None):
            try:
                await self.provider_adapter.cancel(job.provider_job_id)
            except Exception as exc:
                log.warning("Provider cancellation call failed for job %s: %s", job_id, exc)

        return CancellationResult(
            job_id=job_id,
            previous_status=curr_status,
            new_status=target_status,
            is_immediate=False,
            user_message="Your cancellation request has been received.",
        )
