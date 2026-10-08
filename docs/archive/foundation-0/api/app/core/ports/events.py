from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Protocol


@dataclass
class PublishedEvent:
    event_name: str
    payload: dict[str, Any]
    trace_id: str | None = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


class EventPublisherPort(Protocol):
    """Abstract port for asynchronous event publishing (RabbitMQ / Kafka / Redis)."""

    async def publish(
        self,
        event_name: str,
        payload: dict[str, Any],
        trace_id: str | None = None,
    ) -> None:
        """Publish a single domain event."""
        ...

    async def publish_batch(
        self,
        events: list[tuple[str, dict[str, Any]]],
    ) -> None:
        """Publish a batch of domain events."""
        ...


class InMemoryEventPublisher:
    """In-memory event publisher for tests and local development."""

    def __init__(self) -> None:
        self.published: list[PublishedEvent] = []

    async def publish(
        self,
        event_name: str,
        payload: dict[str, Any],
        trace_id: str | None = None,
    ) -> None:
        self.published.append(
            PublishedEvent(event_name=event_name, payload=payload, trace_id=trace_id)
        )

    async def publish_batch(
        self,
        events: list[tuple[str, dict[str, Any]]],
    ) -> None:
        for event_name, payload in events:
            self.published.append(PublishedEvent(event_name=event_name, payload=payload))

    def clear(self) -> None:
        self.published.clear()
