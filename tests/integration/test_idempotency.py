from dataclasses import dataclass
from uuid import uuid4

import pytest

from fashx.core.events import DomainEvent
from fashx.integration.contracts import IntegrationHandler, IntegrationMessage
from fashx.integration.idempotency import IdempotentHandler, InMemoryIdempotencyStore


@dataclass(frozen=True, slots=True)
class DummyEvent(DomainEvent):
    payload: str = ""


class RecordingHandler(IntegrationHandler):
    def __init__(self) -> None:
        self.call_count = 0

    async def handle(self, message: IntegrationMessage) -> None:
        self.call_count += 1


@pytest.mark.asyncio
async def test_idempotent_handler_skips_duplicates():
    store = InMemoryIdempotencyStore()
    inner = RecordingHandler()
    handler = IdempotentHandler(
        consumer_name="orders_consumer",
        handler=inner,
        store=store,
    )

    msg_id = uuid4()
    msg = IntegrationMessage(message_id=msg_id, event=DummyEvent(payload="test"))

    # First dispatch
    await handler.handle(msg)
    assert inner.call_count == 1
    assert await store.has_processed("orders_consumer", msg_id) is True

    # Duplicate dispatch
    await handler.handle(msg)
    assert inner.call_count == 1  # Should not have incremented


@pytest.mark.asyncio
async def test_idempotent_handler_different_consumers():
    store = InMemoryIdempotencyStore()
    inner1 = RecordingHandler()
    inner2 = RecordingHandler()

    h1 = IdempotentHandler(
        consumer_name="consumer_a",
        handler=inner1,
        store=store,
    )
    h2 = IdempotentHandler(
        consumer_name="consumer_b",
        handler=inner2,
        store=store,
    )

    msg_id = uuid4()
    msg = IntegrationMessage(message_id=msg_id, event=DummyEvent(payload="test"))

    await h1.handle(msg)
    await h2.handle(msg)

    assert inner1.call_count == 1
    assert inner2.call_count == 1
