from __future__ import annotations

from collections import defaultdict
from collections.abc import Awaitable, Callable

from .events import DomainEvent, EventEnvelope

EventHandler = Callable[[EventEnvelope], Awaitable[None]]


class EventBus:
    """
    Lightweight async event bus.

    Intended for Core development and testing.
    Production transport can be introduced behind
    the same contract later.
    """

    def __init__(self) -> None:
        self._handlers: defaultdict[str, list[EventHandler]] = defaultdict(list)

    def subscribe(
        self,
        event_type: str,
        handler: EventHandler,
    ) -> None:
        if handler not in self._handlers[event_type]:
            self._handlers[event_type].append(handler)

    async def publish(self, event: DomainEvent) -> None:
        envelope = EventEnvelope(event=event)

        handlers: list[EventHandler] = []
        if event.event_type in self._handlers:
            handlers.extend(self._handlers[event.event_type])

        class_name = event.__class__.__name__
        if class_name != event.event_type and class_name in self._handlers:
            for handler in self._handlers[class_name]:
                if handler not in handlers:
                    handlers.append(handler)

        for handler in handlers:
            await handler(envelope)

    def clear(self) -> None:
        self._handlers.clear()
