"""Unit tests for Stuck-Job Detection, Recovery Sweeper, and Dead-Letter Handling (Phase 07.5).

Covers REC-001 through REC-007 and DLQ-001 through DLQ-006.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from uuid import UUID, uuid4

from fashx.tryon.lifecycle.dead_letter import (
    DeadLetterRecord,
    DeadLetterService,
    DLQStatus,
)
from fashx.tryon.lifecycle.recovery import (
    StuckJobRecoveryService,
    is_job_stuck,
)


class MockDLQRepository:
    def __init__(self) -> None:
        self.records: dict[UUID, DeadLetterRecord] = {}

    async def create_dead_letter(self, record: DeadLetterRecord) -> DeadLetterRecord:
        self.records[record.id] = record
        return record

    async def update_dlq_status(
        self,
        dead_letter_id: UUID,
        status: str,
        resolved_by: str | None = None,
        resolution_note: str | None = None,
        resolved_at: datetime | None = None,
    ) -> bool:
        if dead_letter_id not in self.records:
            return False
        rec = self.records[dead_letter_id]
        updated = DeadLetterRecord(
            id=rec.id,
            job_id=rec.job_id,
            source=rec.source,
            failure_stage=rec.failure_stage,
            error_code=rec.error_code,
            error_summary=rec.error_summary,
            attempt_number=rec.attempt_number,
            payload_reference=rec.payload_reference,
            status=DLQStatus(status),
            created_at=rec.created_at,
            original_message_id=rec.original_message_id,
            resolution_note=resolution_note,
            resolved_by=resolved_by,
            resolved_at=resolved_at,
        )
        self.records[dead_letter_id] = updated
        return True


def test_stuck_job_detection_rules() -> None:
    now = datetime.now(UTC)

    # REC-001: Queued job exceeding 120s threshold
    old_time = now - timedelta(seconds=150)
    stuck, reason = is_job_stuck("QUEUED", created_at=old_time, now=now)
    assert stuck is True
    assert reason == "STUCK_IN_QUEUED"

    # Healthy queued job (30s old)
    fresh_time = now - timedelta(seconds=30)
    stuck_fresh, _ = is_job_stuck("QUEUED", created_at=fresh_time, now=now)
    assert stuck_fresh is False

    # REC-002: Processing job with expired lease
    expired_lease = now - timedelta(seconds=10)
    stuck_lease, reason_lease = is_job_stuck("PROCESSING", lease_expires_at=expired_lease, now=now)
    assert stuck_lease is True
    assert reason_lease == "WORKER_LEASE_EXPIRED"

    # REC-003: SUBMISSION_UNKNOWN older than 120s
    stuck_sub, reason_sub = is_job_stuck("SUBMISSION_UNKNOWN", updated_at=old_time, now=now)
    assert stuck_sub is True
    assert reason_sub == "RECONCILIATION_OVERDUE"

    # REC-004: RETRY_PENDING overdue by > 120s
    overdue_retry = now - timedelta(seconds=150)
    stuck_retry, reason_retry = is_job_stuck("RETRY_PENDING", next_retry_at=overdue_retry, now=now)
    assert stuck_retry is True
    assert reason_retry == "RETRY_DISPATCH_OVERDUE"

    # REC-005: Future retry (not due yet)
    future_retry = now + timedelta(seconds=60)
    stuck_fut, _ = is_job_stuck("RETRY_PENDING", next_retry_at=future_retry, now=now)
    assert stuck_fut is False


async def test_recovery_service_sweeper_actions() -> None:
    now = datetime.now(UTC)
    overdue = now - timedelta(seconds=200)

    jobs = [
        SimpleNamespace(
            id=uuid4(),
            status="QUEUED",
            created_at=overdue,
            updated_at=overdue,
            lease_expires_at=None,
            next_retry_at=None,
        ),
        SimpleNamespace(
            id=uuid4(),
            status="PROCESSING",
            created_at=overdue,
            updated_at=overdue,
            lease_expires_at=now - timedelta(seconds=10),
            next_retry_at=None,
        ),
        SimpleNamespace(
            id=uuid4(),
            status="RETRY_PENDING",
            created_at=overdue,
            updated_at=overdue,
            lease_expires_at=None,
            next_retry_at=overdue,
        ),
        SimpleNamespace(
            id=uuid4(),
            status="SUBMISSION_UNKNOWN",
            created_at=overdue,
            updated_at=overdue,
            lease_expires_at=None,
            next_retry_at=None,
        ),
    ]

    class MockRepo:
        def __init__(self) -> None:
            self.scheduled_reclaim: list[UUID] = []

        async def find_recovery_candidates(self, now: datetime, limit: int = 100) -> list[SimpleNamespace]:
            return jobs

        async def schedule_recovery(self, job_id: UUID, reason: str) -> bool:
            self.scheduled_reclaim.append(job_id)
            return True

    class MockDispatcher:
        def __init__(self) -> None:
            self.dispatched: list[UUID] = []
            self.ensured: list[UUID] = []

        async def dispatch(self, job_id: UUID) -> None:
            self.dispatched.append(job_id)

        async def ensure_dispatched(self, job_id: UUID) -> None:
            self.ensured.append(job_id)

    repo = MockRepo()
    disp = MockDispatcher()
    service = StuckJobRecoveryService(repository=repo, dispatcher=disp)

    actions = await service.scan_and_recover_due_jobs(now=now)

    assert len(actions) == 4
    # REC-001: Queued -> ensure_dispatched
    assert disp.ensured == [jobs[0].id]
    # REC-002: Processing lease expired -> schedule_recovery
    assert repo.scheduled_reclaim == [jobs[1].id]
    # REC-004: Retry pending -> dispatch
    assert disp.dispatched == [jobs[2].id]
    # REC-003: Submission unknown -> scheduled reconciliation
    assert actions[3].action_type == "SCHEDULE_RECONCILIATION"


async def test_dead_letter_service_capture_and_replay() -> None:
    # DLQ-001, DLQ-003, DLQ-005
    repo = MockDLQRepository()
    service = DeadLetterService(dlq_repository=repo)

    job_id = uuid4()
    # Sensitive fields to be sanitized
    payload = {
        "job_id": str(job_id),
        "authorization": "Bearer secret-token-12345",
        "api_key": "live_fashn_secret_key",
        "category": "tops",
    }

    rec = await service.record_dead_letter(
        job_id=job_id,
        source="CELERY_WORKER",
        failure_stage="DOWNLOADING_OUTPUT",
        error_code="PROVIDER_DOWNLOAD_FAILED",
        error_summary="Timeout downloading output image",
        attempt_number=3,
        payload_reference=payload,
    )

    assert rec.id in repo.records
    assert rec.status == DLQStatus.OPEN
    # Verify sensitive fields sanitized out
    assert "authorization" not in rec.payload_reference
    assert "api_key" not in rec.payload_reference
    assert rec.payload_reference["category"] == "tops"

    # DLQ-005: Operator controlled replay
    replayed = await service.replay_dead_letter(
        dead_letter_id=rec.id,
        operator_id="operator-alice",
        note="Inspected provider status; safe to re-download",
    )
    assert replayed is True
    assert repo.records[rec.id].status == DLQStatus.REPLAYED
    assert repo.records[rec.id].resolved_by == "operator-alice"
