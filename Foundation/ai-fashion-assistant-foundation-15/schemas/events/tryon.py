from schemas.events.base import DomainEvent


class TryOnCompleted(DomainEvent):
    event_type: str = "tryon_completed"


class TryOnFailed(DomainEvent):
    event_type: str = "tryon_failed"
