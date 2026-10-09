from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.operations import IdempotencyRecord


class IdempotencyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, *, user_id: UUID, key: str) -> IdempotencyRecord | None:
        statement = select(IdempotencyRecord).where(
            IdempotencyRecord.user_id == user_id,
            IdempotencyRecord.key == key,
        )
        return (await self.session.execute(statement)).scalar_one_or_none()

    async def create_claim(self, *, user_id: UUID, key: str, request_hash: str) -> IdempotencyRecord:
        record = IdempotencyRecord(user_id=user_id, key=key, request_hash=request_hash, state="in_progress")
        self.session.add(record)
        await self.session.flush()
        return record

    async def complete(self, record: IdempotencyRecord, *, status_code: int, response_body: dict) -> None:
        record.status_code = status_code
        record.response_body = response_body
        record.state = "completed"
        await self.session.flush()


class InMemoryIdempotencyRepository:
    """In-memory idempotency repository for testing."""

    def __init__(self) -> None:
        self._records: dict[tuple[UUID, str], IdempotencyRecord] = {}

    async def get(self, *, user_id: UUID, key: str) -> IdempotencyRecord | None:
        return self._records.get((user_id, key))

    async def create_claim(self, *, user_id: UUID, key: str, request_hash: str) -> IdempotencyRecord:
        record = IdempotencyRecord(
            user_id=user_id, key=key, request_hash=request_hash, state="in_progress"
        )
        self._records[(user_id, key)] = record
        return record

    async def complete(self, record: IdempotencyRecord, *, status_code: int, response_body: dict) -> None:
        record.status_code = status_code
        record.response_body = response_body
        record.state = "completed"
        self._records[(record.user_id, record.key)] = record
