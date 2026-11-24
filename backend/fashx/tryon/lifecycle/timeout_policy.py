"""VTO Timeout Policy, Worker Leases, and Heartbeat Invariants (Phase 07.5)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4


class LeaseLostError(Exception):
    """Raised when a worker attempts an update after losing its ownership lease."""

    def __init__(self, job_id: UUID, worker_id: str, reason: str = "Lease expired or reclaimed") -> None:
        self.job_id = job_id
        self.worker_id = worker_id
        self.reason = reason
        super().__init__(f"Worker {worker_id} lost lease on job {job_id}: {reason}")


class StaleVersionError(Exception):
    """Raised when an update fails because another process changed the optimistic version."""

    def __init__(self, job_id: UUID, expected_version: int) -> None:
        self.job_id = job_id
        self.expected_version = expected_version
        super().__init__(f"Job {job_id} optimistic concurrency failure: expected version {expected_version}")


@dataclass(frozen=True)
class TimeoutPolicy:
    """Configured operational deadlines and timeouts across the lifecycle."""

    worker_lease_seconds: int = 60
    worker_heartbeat_seconds: int = 15
    provider_connect_seconds: float = 5.0
    provider_request_seconds: float = 30.0
    provider_inference_deadline_seconds: float = 180.0
    output_download_seconds: float = 30.0
    whole_job_deadline_seconds: float = 300.0  # 5 minutes


DEFAULT_TIMEOUT_POLICY = TimeoutPolicy()


@dataclass(frozen=True)
class WorkerLease:
    """Active worker lease token and expiry."""

    worker_id: str
    lease_token: UUID
    lease_expires_at: datetime
    heartbeat_at: datetime

    @classmethod
    def create(
        cls,
        worker_id: str,
        lease_seconds: int = 60,
        now: datetime | None = None,
    ) -> WorkerLease:
        now_ts = now or datetime.now(UTC)
        return cls(
            worker_id=worker_id,
            lease_token=uuid4(),
            lease_expires_at=now_ts + timedelta(seconds=lease_seconds),
            heartbeat_at=now_ts,
        )

    def is_expired(self, now: datetime | None = None) -> bool:
        now_ts = now or datetime.now(UTC)
        return now_ts >= self.lease_expires_at
