"""VTO Job Lifecycle Engine and Reliability Coordinator (Phase 07.5)."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from fashx.tryon.lifecycle.dead_letter import DeadLetterService
from fashx.tryon.lifecycle.errors import ErrorCode, classify_error
from fashx.tryon.lifecycle.retry_policy import (
    WORKER_EXECUTION_POLICY,
    RetryPolicy,
    compute_next_retry_at,
    retry_allowed,
)
from fashx.tryon.lifecycle.states import JobStatus
from fashx.tryon.lifecycle.timeout_policy import LeaseLostError, StaleVersionError, WorkerLease
from fashx.tryon.lifecycle.transitions import validate_transition

log = logging.getLogger(__name__)


class JobLifecycleService:
    """Coordinates state transitions, optimistic locking, retries, and failure auditing."""

    def __init__(
        self,
        tryon_uow: Any,
        dead_letter_service: DeadLetterService | None = None,
    ) -> None:
        self.tryon_uow = tryon_uow
        self.dlq_service = dead_letter_service

    async def transition_job(
        self,
        *,
        job_id: UUID,
        expected_status: str | JobStatus,
        target_status: str | JobStatus,
        expected_version: int | None = None,
        worker_id: str | None = None,
        lease_token: UUID | None = None,
        actor_type: str = "WORKER",
        reason_code: str | None = None,
        metadata: dict[str, Any] | None = None,
        now: datetime | None = None,
    ) -> bool:
        """Atomically transition job status enforcing transition validity and optimistic versioning.

        Also persists append-only transition event in tryon_job_events.
        """
        now_ts = now or datetime.now(UTC)
        curr_enum, target_enum = validate_transition(expected_status, target_status)

        success = await self.tryon_uow.jobs.transition_with_version_and_event(
            job_id=job_id,
            expected_status=curr_enum.value,
            target_status=target_enum.value,
            expected_version=expected_version,
            worker_id=worker_id,
            lease_token=lease_token,
            actor_type=actor_type,
            reason_code=reason_code,
            metadata=metadata or {},
            now=now_ts,
        )

        if not success:
            job = await self.tryon_uow.jobs.get_by_id(job_id)
            if job and worker_id and getattr(job, "worker_id", None) != worker_id:
                raise LeaseLostError(job_id, worker_id)
            if job and expected_version is not None and getattr(job, "version", 1) != expected_version:
                raise StaleVersionError(job_id, expected_version)
            return False

        return True

    async def schedule_retry(
        self,
        *,
        job_id: UUID,
        error_code: ErrorCode | str,
        operation_policy: RetryPolicy = WORKER_EXECUTION_POLICY,
        retry_after_seconds: float | None = None,
        now: datetime | None = None,
    ) -> bool:
        """Evaluate error and schedule retry or transition to FAILED with dead letter."""
        now_ts = now or datetime.now(UTC)
        job = await self.tryon_uow.jobs.get_by_id(job_id)
        if not job:
            return False

        definition = classify_error(error_code)
        current_retries = getattr(job, "retry_count", 0) or 0

        can_retry = retry_allowed(
            retry_count=current_retries,
            policy=operation_policy,
            retryable=definition.retryable,
            safe_to_repeat=definition.safe_to_repeat,
        )

        if can_retry:
            next_retry = compute_next_retry_at(
                retry_count=current_retries,
                policy=operation_policy,
                retry_after_seconds=retry_after_seconds,
                now=now_ts,
            )
            # Transition to RETRY_PENDING
            await self.tryon_uow.jobs.update_retry_pending(
                job_id=job_id,
                retry_count=current_retries + 1,
                next_retry_at=next_retry,
                last_error_code=definition.code.value,
                now=now_ts,
            )
            log.info("Job %s scheduled for retry %d at %s", job_id, current_retries + 1, next_retry)
            return True

        # Retries denied or exhausted -> transition to FAILED
        final_code = (
            ErrorCode.MAX_RETRIES_EXCEEDED.value
            if (definition.retryable and current_retries >= operation_policy.max_retries)
            else definition.code.value
        )

        await self.tryon_uow.jobs.update_status_and_event(
            job_id=job_id,
            expected_status=job.status,
            new_status=JobStatus.FAILED.value,
            actor_type="SYSTEM",
            reason_code=final_code,
            metadata={"exhausted": current_retries >= operation_policy.max_retries, "last_error": definition.code.value},
            now=now_ts,
        )

        if self.dlq_service:
            await self.dlq_service.record_dead_letter(
                job_id=job_id,
                source="WORKER_RETRY_EXHAUSTED",
                failure_stage=getattr(job, "progress_stage", "PROCESSING") or "PROCESSING",
                error_code=final_code,
                error_summary=definition.description,
                attempt_number=current_retries,
                payload_reference={"job_id": str(job_id), "retries": current_retries},
                now=now_ts,
            )

        return False

    async def claim_job_with_lease(
        self,
        *,
        job_id: UUID,
        worker_id: str,
        lease_seconds: int = 60,
        now: datetime | None = None,
    ) -> WorkerLease | None:
        """Atomically claim a QUEUED or RETRY_PENDING job using a lease token."""
        now_ts = now or datetime.now(UTC)
        lease = WorkerLease.create(worker_id=worker_id, lease_seconds=lease_seconds, now=now_ts)

        claimed = await self.tryon_uow.jobs.claim_with_lease(
            job_id=job_id,
            worker_id=worker_id,
            lease_token=lease.lease_token,
            lease_expires_at=lease.lease_expires_at,
            now=now_ts,
        )

        if not claimed:
            return None

        return lease
