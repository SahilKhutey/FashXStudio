from datetime import datetime, timezone
from uuid import uuid4

from schemas.events.base import DomainEvent
from schemas.events.tryon import TryOnCompleted, TryOnFailed, TryOnStarted, TryOnViewed


def test_tryon_event_types_are_stable() -> None:
    assert TryOnStarted.model_fields["event_type"].default == "tryon_started"
    assert TryOnViewed.model_fields["event_type"].default == "tryon_viewed"
    assert TryOnCompleted.model_fields["event_type"].default == "tryon_completed"
    assert TryOnFailed.model_fields["event_type"].default == "tryon_failed"


def test_domain_event_preserves_traceability() -> None:
    event = DomainEvent(
        event_id=uuid4(), event_type="tryon_viewed", user_id=uuid4(), object_type="tryon_job",
        object_id=uuid4(), trace_id=uuid4(), occurred_at=datetime.now(timezone.utc), payload={"screen_context": "result"},
    )
    assert event.trace_id is not None
    assert event.object_type == "tryon_job"
    assert event.payload["screen_context"] == "result"
