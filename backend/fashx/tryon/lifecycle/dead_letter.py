"""VTO Dead-Letter Handling and Investigation Service (Phase 07.5)."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

log = logging.getLogger(__name__)


class DLQStatus(StrEnum):
    OPEN = "OPEN"
    INVESTIGATING = "INVESTIGATING"
    REPLAYED = "REPLAYED"
    DISCARDED = "DISCARDED"
    RESOLVED = "RESOLVED"


@dataclass(frozen=True)
class DeadLetterRecord:
    id: UUID
    job_id: UUID | None
    source: str
    failure_stage: str
    error_code: str
    error_summary: str
    attempt_number: int
    payload_reference: dict[str, Any]
    status: DLQStatus
    created_at: datetime
    original_message_id: str | None = None
    resolution_note: str | None = None
    resolved_by: str | None = None
    resolved_at: datetime | None = None


class DeadLetterService:
    """Manages dead-letter capture for unrecoverable errors, exhausted retries, and invalid messages."""

    def __init__(self, dlq_repository: Any) -> None:
        self.dlq_repository = dlq_repository

    async def record_dead_letter(
        self,
        *,
        job_id: UUID | None,
        source: str,
        failure_stage: str,
        error_code: str,
        error_summary: str,
        attempt_number: int = 0,
        payload_reference: dict[str, Any] | None = None,
        original_message_id: str | None = None,
        now: datetime | None = None,
    ) -> DeadLetterRecord:
        """Idempotently persist a dead-letter entry for operations triage.

        Sanitizes payload reference to exclude raw image data, auth headers, and secrets.
        """
        now_ts = now or datetime.now(UTC)

        # Sanitize payload reference
        safe_payload = {}
        if payload_reference:
            for k, v in payload_reference.items():
                if k.lower() in {"authorization", "token", "api_key", "secret", "image_bytes", "presigned_url"}:
                    continue
                safe_payload[k] = str(v)[:256]

        record = DeadLetterRecord(
            id=uuid4(),
            job_id=job_id,
            source=source,
            failure_stage=failure_stage,
            error_code=error_code,
            error_summary=error_summary[:500],
            attempt_number=max(0, attempt_number),
            payload_reference=safe_payload,
            status=DLQStatus.OPEN,
            created_at=now_ts,
            original_message_id=original_message_id,
        )

        return await self.dlq_repository.create_dead_letter(record)

    async def replay_dead_letter(
        self,
        dead_letter_id: UUID,
        *,
        operator_id: str,
        note: str,
        now: datetime | None = None,
    ) -> bool:
        """Mark dead letter as REPLAYED following verified operator inspection."""
        now_ts = now or datetime.now(UTC)
        return await self.dlq_repository.update_dlq_status(
            dead_letter_id=dead_letter_id,
            status=DLQStatus.REPLAYED.value,
            resolved_by=operator_id,
            resolution_note=note,
            resolved_at=now_ts,
        )
