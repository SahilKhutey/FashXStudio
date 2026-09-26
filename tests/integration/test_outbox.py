from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.core.events import DomainEvent
from app.integration.outbox import InMemoryOutboxRepository, OutboxMessage


@dataclass(frozen=True, slots=True)
class DummyEvent(DomainEvent):
    info: str = ""


@pytest.mark.asyncio
async def test_outbox_repository_add_and_pending():
    repo = InMemoryOutboxRepository()

    msg1 = OutboxMessage(
        id=uuid4(),
        event=DummyEvent(info="event 1"),
        created_at=datetime.now(UTC),
    )
    msg2 = OutboxMessage(
        id=uuid4(),
        event=DummyEvent(info="event 2"),
        created_at=datetime.now(UTC),
    )

    await repo.add(msg1)
    await repo.add(msg2)

    pending = await repo.pending(limit=10)
    assert len(pending) == 2
    assert pending[0].id == msg1.id
    assert pending[1].id == msg2.id


@pytest.mark.asyncio
async def test_outbox_repository_mark_published():
    repo = InMemoryOutboxRepository()

    msg = OutboxMessage(
        id=uuid4(),
        event=DummyEvent(info="event 1"),
        created_at=datetime.now(UTC),
    )
    await repo.add(msg)

    pending = await repo.pending()
    assert len(pending) == 1

    await repo.mark_published(msg.id)

    pending_after = await repo.pending()
    assert len(pending_after) == 0


@pytest.mark.asyncio
async def test_outbox_repository_limit():
    repo = InMemoryOutboxRepository()

    for i in range(5):
        msg = OutboxMessage(
            id=uuid4(),
            event=DummyEvent(info=f"event {i}"),
            created_at=datetime.now(UTC),
        )
        await repo.add(msg)

    pending = await repo.pending(limit=3)
    assert len(pending) == 3
