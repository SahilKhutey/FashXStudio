from schemas.events.base import DomainEvent


class TryOnStarted(DomainEvent):
    event_type: str = "tryon_started"
    object_type: str = "tryon_job"


class TryOnViewed(DomainEvent):
    event_type: str = "tryon_viewed"
    object_type: str = "tryon_job"


class TryOnRetryRequested(DomainEvent):
    event_type: str = "tryon_retry_requested"
    object_type: str = "tryon_job"


class TryOnCancelled(DomainEvent):
    event_type: str = "tryon_cancelled"
    object_type: str = "tryon_job"


class TryOnCompleted(DomainEvent):
    event_type: str = "tryon_completed"
    object_type: str = "tryon_job"


class TryOnFailed(DomainEvent):
    event_type: str = "tryon_failed"
    object_type: str = "tryon_job"
