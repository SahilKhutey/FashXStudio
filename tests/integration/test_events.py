from dataclasses import dataclass
from uuid import uuid4

import pytest

from app.core.errors import DependencyError
from app.core.events import DomainEvent
from app.integration.contracts import IntegrationHandler, IntegrationMessage
from app.integration.dispatcher import IntegrationDispatcher


@dataclass(frozen=True, slots=True)
class SampleIntegrationEvent(DomainEvent):
    item_id: str = ""


class SuccessfulHandler(IntegrationHandler):
    def __init__(self) -> None:
        self.handled_messages: list[IntegrationMessage] = []

    async def handle(self, message: IntegrationMessage) -> None:
        self.handled_messages.append(message)


class FailingHandler(IntegrationHandler):
    async def handle(self, message: IntegrationMessage) -> None:
        raise RuntimeError("Handler execution crashed")


@pytest.mark.asyncio
async def test_integration_dispatcher_success():
    dispatcher = IntegrationDispatcher()
    handler = SuccessfulHandler()
    dispatcher.register(SampleIntegrationEvent, handler)

    event = SampleIntegrationEvent(item_id="item-123")
    msg = IntegrationMessage(message_id=uuid4(), event=event)

    await dispatcher.dispatch(msg)

    assert len(handler.handled_messages) == 1
    assert handler.handled_messages[0] == msg


@pytest.mark.asyncio
async def test_integration_dispatcher_dependency_error_wrapping():
    dispatcher = IntegrationDispatcher()
    failing_handler = FailingHandler()
    dispatcher.register(SampleIntegrationEvent, failing_handler)

    event = SampleIntegrationEvent(item_id="item-fail")
    msg = IntegrationMessage(message_id=uuid4(), event=event)

    with pytest.raises(DependencyError) as exc_info:
        await dispatcher.dispatch(msg)

    err = exc_info.value
    assert "Integration handler failed." in str(err)
    assert err.details.get("event") == "SampleIntegrationEvent"
    assert err.details.get("handler") == "FailingHandler"
