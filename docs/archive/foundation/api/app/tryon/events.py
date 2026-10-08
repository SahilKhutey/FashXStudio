from __future__ import annotations
from datetime import datetime, timezone
from uuid import UUID, uuid4
from api.app.events.repository import EventRepository

async def record_tryon_event(session, *, event_type: str, user_id: UUID, job_id: UUID,
                             trace_id: UUID | None, payload: dict[str, object] | None = None) -> None:
    await EventRepository(session).create(
        event_id=uuid4(), event_type=event_type, schema_version=1,
        user_id=user_id, object_type="tryon_job", object_id=job_id,
        trace_id=trace_id, occurred_at=datetime.now(timezone.utc), payload=payload or {},
    )
