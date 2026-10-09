from datetime import UTC, datetime
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from database.models import Base
from fashx.core.events import DomainEvent, EntityCreated
from fashx.integration.outbox import (
    InMemoryOutboxRepository,
    OutboxMessage,
    OutboxRepository,
    SqlOutboxRepository,
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
def outbox_repo(request, sqlite_session) -> OutboxRepository:
    if request.param == "memory":
        return InMemoryOutboxRepository()
    return SqlOutboxRepository(sqlite_session)


@pytest.mark.asyncio
async def test_outbox_add_and_pending(outbox_repo: OutboxRepository) -> None:
    msg_id = uuid4()
    msg = OutboxMessage(
        id=msg_id,
        event=EntityCreated(entity_type="test.event", entity_id=msg_id),
        created_at=datetime.now(UTC),
    )
    await outbox_repo.add(msg)

    pending = await outbox_repo.pending()
    assert len(pending) == 1
    assert pending[0].id == msg_id
    assert pending[0].event.event_type == "EntityCreated"


@pytest.mark.asyncio
async def test_outbox_claim_and_mark_published(outbox_repo: OutboxRepository) -> None:
    msg_id = uuid4()
    msg = OutboxMessage(
        id=msg_id,
        event=EntityCreated(entity_type="test.claim", entity_id=msg_id),
        created_at=datetime.now(UTC),
    )
    await outbox_repo.add(msg)

    claimed = await outbox_repo.claim(limit=10)
    assert len(claimed) == 1
    assert claimed[0].attempts == 1

    await outbox_repo.mark_published(msg_id)
    pending = await outbox_repo.pending()
    assert len(pending) == 0
