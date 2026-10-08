from __future__ import annotations

from uuid import uuid4

import pytest

from fashx.application.idempotency import IdempotencyService
from api.app.core.errors import ConflictError
from fashx.repositories.idempotency import IdempotencyRepository


class _Result:
    def __init__(self, value) -> None:
        self.value = value

    def scalar_one_or_none(self):
        return self.value


class FakeSession:
    def __init__(self) -> None:
        self.records = {}
        self.commits = 0
        self.rollbacks = 0

    def add(self, entity) -> None:
        self.records[(entity.user_id, entity.key)] = entity

    async def flush(self) -> None:
        return None

    async def execute(self, _statement):
        return _Result(next(iter(self.records.values()), None))

    async def commit(self) -> None:
        self.commits += 1

    async def rollback(self) -> None:
        self.rollbacks += 1


@pytest.mark.asyncio
async def test_idempotency_service_claims_once() -> None:
    session = FakeSession()
    repository = IdempotencyRepository.__new__(IdempotencyRepository)
    repository.session = session  # type: ignore[assignment]
    service = IdempotencyService(repository)
    user_id = uuid4()

    first = await service.acquire(user_id=user_id, key="k1", request_parts=("garment", "1"))
    assert first.replay is False

    with pytest.raises(ConflictError):
        await service.acquire(user_id=user_id, key="k1", request_parts=("garment", "2"))

    assert session.commits == 1
    assert session.rollbacks == 1
