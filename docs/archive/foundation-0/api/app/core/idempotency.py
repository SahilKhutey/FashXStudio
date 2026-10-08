import asyncio
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from .errors import IdempotencyConflictError


class IdempotencyStatus(StrEnum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class IdempotencyRecord:
    status: IdempotencyStatus
    payload_hash: str
    status_code: int | None = None
    response_data: Any = None


@dataclass
class ClaimResult:
    claimed: bool
    cached_status_code: int | None = None
    cached_response: Any = None


class IdempotencyManager:
    """Manages request idempotency to prevent duplicate mutations (Rule I08)."""

    def __init__(self) -> None:
        self._records: dict[str, IdempotencyRecord] = {}
        self._lock = asyncio.Lock()

    async def claim(self, key: str, payload_hash: str) -> ClaimResult:
        """Attempt to claim an idempotency key.

        Returns ClaimResult(claimed=True) if newly claimed.
        Returns ClaimResult(claimed=False, cached_...) if previously completed with matching hash.
        Raises IdempotencyConflictError if in-progress or payload hash mismatches.
        """
        async with self._lock:
            record = self._records.get(key)
            if record is None or record.status == IdempotencyStatus.FAILED:
                self._records[key] = IdempotencyRecord(
                    status=IdempotencyStatus.IN_PROGRESS,
                    payload_hash=payload_hash,
                )
                return ClaimResult(claimed=True)

            if record.status == IdempotencyStatus.IN_PROGRESS:
                raise IdempotencyConflictError(
                    f"A request with idempotency key '{key}' is currently in progress."
                )

            if record.status == IdempotencyStatus.COMPLETED:
                if record.payload_hash != payload_hash:
                    raise IdempotencyConflictError(
                        f"Idempotency key '{key}' was previously used with different parameters."
                    )
                return ClaimResult(
                    claimed=False,
                    cached_status_code=record.status_code,
                    cached_response=record.response_data,
                )

            return ClaimResult(claimed=True)

    async def complete(self, key: str, status_code: int, response_data: Any) -> None:
        """Complete an idempotency record and persist response for replay."""
        async with self._lock:
            if key in self._records:
                self._records[key].status = IdempotencyStatus.COMPLETED
                self._records[key].status_code = status_code
                self._records[key].response_data = response_data

    async def fail(self, key: str) -> None:
        """Mark record as failed so retry is allowed."""
        async with self._lock:
            if key in self._records:
                self._records[key].status = IdempotencyStatus.FAILED

    async def clear(self) -> None:
        """Clear records (useful in test teardown)."""
        async with self._lock:
            self._records.clear()


# Default singleton manager instance
default_idempotency_manager = IdempotencyManager()
