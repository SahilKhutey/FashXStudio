from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from fashx.core.errors import ConflictError
from fashx.core.idempotency import request_fingerprint
from fashx.core.transactions import transaction
from fashx.repositories.idempotency import IdempotencyRepository


@dataclass(frozen=True, slots=True)
class IdempotencyResult:
    replay: bool
    response: dict | None = None
    status_code: int | None = None


class IdempotencyService:
    """Application-level idempotency primitive shared by expensive POST operations."""

    def __init__(self, repository: IdempotencyRepository) -> None:
        self.repository = repository

    async def acquire(self, *, user_id: UUID, key: str, request_parts: tuple[object, ...]) -> IdempotencyResult:
        fingerprint = request_fingerprint(*request_parts)
        async with transaction(self.repository.session):
            existing = await self.repository.get(user_id=user_id, key=key)
            if existing is not None:
                if existing.request_hash != fingerprint:
                    raise ConflictError("Idempotency-Key was already used with a different request")
                if existing.state == "completed":
                    return IdempotencyResult(
                        replay=True,
                        response=existing.response_body,
                        status_code=existing.status_code,
                    )
                raise ConflictError("The same request is already being processed")
            await self.repository.create_claim(user_id=user_id, key=key, request_hash=fingerprint)
            return IdempotencyResult(replay=False)
