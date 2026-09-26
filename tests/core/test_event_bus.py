import pytest

from app.core.event_bus import EventBus
from app.core.events import EntityCreated


@pytest.mark.asyncio
async def test_event_bus_delivers_event():
    bus = EventBus()
    received = []

    async def handler(envelope):
        received.append(envelope.event)

    bus.subscribe("EntityCreated", handler)

    event = EntityCreated(entity_type="product")

    await bus.publish(event)

    assert len(received) == 1
    assert received[0] is event
