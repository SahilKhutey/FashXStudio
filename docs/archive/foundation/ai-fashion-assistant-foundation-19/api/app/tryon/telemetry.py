from __future__ import annotations
from datetime import datetime, timezone
from uuid import UUID, uuid4
from api.app.core.errors import NotFoundError
from api.app.core.transactions import transaction
from api.app.events.repository import EventRepository
from api.app.tryon.repositories.tryon import TryOnRepository
from schemas.tryon.telemetry import TryOnTelemetryCreate, TryOnTelemetryResponse

class TryOnTelemetryService:
    def __init__(self, session, tryon: TryOnRepository) -> None:
        self.session = session
        self.tryon = tryon

    async def record(self, *, user_id: UUID, job_id: UUID, request: TryOnTelemetryCreate, trace_id: UUID | None) -> TryOnTelemetryResponse:
        async with transaction(self.session):
            job = await self.tryon.get_by_id_for_user(user_id=user_id, job_id=job_id)
            if job is None:
                raise NotFoundError("Try-on job not found")
            await EventRepository(self.session).create(
                event_id=uuid4(), event_type=f"tryon_{request.event.value}", schema_version=1,
                user_id=user_id, object_type="tryon_job", object_id=job_id, trace_id=trace_id,
                occurred_at=datetime.now(timezone.utc),
                payload={"elapsed_ms": request.elapsed_ms, "screen_context": request.screen_context},
            )
            return TryOnTelemetryResponse(accepted=True)
