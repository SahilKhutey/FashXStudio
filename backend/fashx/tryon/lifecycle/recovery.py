"""VTO Stuck-Job Detection, Thresholds, and Recovery Sweeper (Phase 07.5)."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from fashx.tryon.lifecycle.states import JobStatus

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class StuckThresholds:
    """Configured thresholds beyond which a job is marked stuck and candidate for recovery."""

    created_seconds: float = 30.0
    validating_seconds: float = 60.0
    queued_seconds: float = 120.0
    processing_lease_expired_seconds: float = 0.0  # Immediate once lease_expires_at <= now
    submission_unknown_seconds: float = 120.0
    retry_pending_overdue_seconds: float = 120.0
    output_validating_seconds: float = 60.0
    storing_result_seconds: float = 120.0
    cancel_requested_seconds: float = 120.0


DEFAULT_STUCK_THRESHOLDS = StuckThresholds()


def is_job_stuck(
    status: JobStatus | str,
    *,
    created_at: datetime | None = None,
    updated_at: datetime | None = None,
    lease_expires_at: datetime | None = None,
    next_retry_at: datetime | None = None,
    now: datetime | None = None,
    thresholds: StuckThresholds = DEFAULT_STUCK_THRESHOLDS,
) -> tuple[bool, str]:
    """Evaluate whether a job is stuck based on its status and timestamps.

    Returns: (is_stuck, reason_code)
    """
    now_ts = now or datetime.now(UTC)
    status_str = str(status).upper()

    if status_str == JobStatus.CREATED.value:
        if created_at and (now_ts - created_at) > timedelta(seconds=thresholds.created_seconds):
            return True, "STUCK_IN_CREATED"

    elif status_str == JobStatus.VALIDATING.value:
        last_activity = updated_at or created_at
        if last_activity and (now_ts - last_activity) > timedelta(seconds=thresholds.validating_seconds):
            return True, "STUCK_IN_VALIDATING"

    elif status_str == JobStatus.QUEUED.value:
        last_activity = updated_at or created_at
        if last_activity and (now_ts - last_activity) > timedelta(seconds=thresholds.queued_seconds):
            return True, "STUCK_IN_QUEUED"

    elif status_str == JobStatus.PROCESSING.value:
        if lease_expires_at and now_ts >= lease_expires_at:
            return True, "WORKER_LEASE_EXPIRED"

    elif status_str == JobStatus.SUBMISSION_UNKNOWN.value:
        last_activity = updated_at or created_at
        if last_activity and (now_ts - last_activity) > timedelta(seconds=thresholds.submission_unknown_seconds):
            return True, "RECONCILIATION_OVERDUE"

    elif status_str == JobStatus.RETRY_PENDING.value:
        if next_retry_at and (now_ts - next_retry_at) > timedelta(seconds=thresholds.retry_pending_overdue_seconds):
            return True, "RETRY_DISPATCH_OVERDUE"

    elif status_str == JobStatus.OUTPUT_VALIDATING.value:
        last_activity = updated_at or created_at
        if last_activity and (now_ts - last_activity) > timedelta(seconds=thresholds.output_validating_seconds):
            return True, "STUCK_IN_OUTPUT_VALIDATION"

    elif status_str == JobStatus.STORING_RESULT.value:
        last_activity = updated_at or created_at
        if last_activity and (now_ts - last_activity) > timedelta(seconds=thresholds.storing_result_seconds):
            return True, "STUCK_IN_STORING_RESULT"

    elif status_str == JobStatus.CANCEL_REQUESTED.value:
        last_activity = updated_at or created_at
        if last_activity and (now_ts - last_activity) > timedelta(seconds=thresholds.cancel_requested_seconds):
            return True, "STUCK_IN_CANCEL_REQUESTED"

    return False, "HEALTHY"


@dataclass
class RecoveryAction:
    job_id: UUID
    status: JobStatus
    action_type: str
    reason: str


class StuckJobRecoveryService:
    """Orchestrates detection and recovery of stalled or unprogressed try-on jobs."""

    def __init__(self, repository: Any, dispatcher: Any | None = None) -> None:
        self.repository = repository
        self.dispatcher = dispatcher

    async def scan_and_recover_due_jobs(
        self,
        limit: int = 100,
        now: datetime | None = None,
    ) -> list[RecoveryAction]:
        now_ts = now or datetime.now(UTC)
        candidates = await self.repository.find_recovery_candidates(now=now_ts, limit=limit)
        actions: list[RecoveryAction] = []

        for job in candidates:
            stuck, reason = is_job_stuck(
                job.status,
                created_at=job.created_at,
                updated_at=getattr(job, "updated_at", None),
                lease_expires_at=getattr(job, "lease_expires_at", None),
                next_retry_at=getattr(job, "next_retry_at", None),
                now=now_ts,
            )
            if not stuck:
                continue

            status_val = JobStatus(job.status.upper()) if isinstance(job.status, str) else job.status

            if status_val == JobStatus.RETRY_PENDING:
                if self.dispatcher and hasattr(self.dispatcher, "dispatch"):
                    await self.dispatcher.dispatch(job.id)
                actions.append(RecoveryAction(job.id, status_val, "DISPATCH_RETRY", reason))

            elif status_val == JobStatus.QUEUED:
                if self.dispatcher and hasattr(self.dispatcher, "ensure_dispatched"):
                    await self.dispatcher.ensure_dispatched(job.id)
                actions.append(RecoveryAction(job.id, status_val, "REDELIVER_QUEUED", reason))

            elif status_val == JobStatus.PROCESSING:
                # Expired lease: reclaim and reschedule
                await self.repository.schedule_recovery(job.id, reason=reason)
                actions.append(RecoveryAction(job.id, status_val, "RECLAIM_EXPIRED_LEASE", reason))

            elif status_val == JobStatus.SUBMISSION_UNKNOWN:
                # Requires reconciliation task, never duplicate paid POST
                actions.append(RecoveryAction(job.id, status_val, "SCHEDULE_RECONCILIATION", reason))

            else:
                actions.append(RecoveryAction(job.id, status_val, "FLAGGED_FOR_TRIAGE", reason))

        return actions
