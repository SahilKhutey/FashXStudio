from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from database.models import Base
from database.models.identity import User
from fashx.repositories.idempotency import (
    IdempotencyRepository,
    InMemoryIdempotencyRepository,
)


@pytest_asyncio.fixture
async def sqlite_session() -> AsyncSession:
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    await engine.dispose()


@pytest.fixture(params=["memory", "sql"])
def idempotency_repo(request, sqlite_session):
    if request.param == "memory":
        return InMemoryIdempotencyRepository()
    return IdempotencyRepository(sqlite_session)


@pytest.mark.asyncio
async def test_idempotency_claim_and_complete(idempotency_repo, sqlite_session) -> None:
    user_id = uuid4()
    # Seed user in SQL session if running sql adapter
    if isinstance(idempotency_repo, IdempotencyRepository):
        sqlite_session.add(User(id=user_id))
        await sqlite_session.flush()

    key = "req-123"
    req_hash = "abcde12345"

    claim = await idempotency_repo.create_claim(user_id=user_id, key=key, request_hash=req_hash)
    assert claim.user_id == user_id
    assert claim.key == key
    assert claim.state == "in_progress"

    existing = await idempotency_repo.get(user_id=user_id, key=key)
    assert existing is not None
    assert existing.request_hash == req_hash

    await idempotency_repo.complete(existing, status_code=200, response_body={"success": True})
    updated = await idempotency_repo.get(user_id=user_id, key=key)
    assert updated is not None
    assert updated.state == "completed"
    assert updated.status_code == 200
    assert updated.response_body == {"success": True}
