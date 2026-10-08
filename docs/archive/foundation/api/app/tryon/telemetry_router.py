from uuid import UUID
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from api.app.auth.dependencies import current_user_id
from api.app.core.dependencies import db_session
from api.app.tryon.repositories.tryon import TryOnRepository
from api.app.tryon.telemetry import TryOnTelemetryService
from schemas.tryon.telemetry import TryOnTelemetryCreate, TryOnTelemetryResponse

router = APIRouter(prefix="/api/v1/tryon", tags=["try-on-telemetry"])

@router.post("/{job_id}/telemetry", response_model=TryOnTelemetryResponse)
async def telemetry(
    job_id: UUID,
    payload: TryOnTelemetryCreate,
    request: Request,
    user_id: UUID = Depends(current_user_id),
    session: AsyncSession = Depends(db_session),
) -> TryOnTelemetryResponse:
    service = TryOnTelemetryService(session, TryOnRepository(session))
    trace_raw = getattr(request.state, "trace_id", None)
    trace_id = UUID(trace_raw) if trace_raw else None
    return await service.record(user_id=user_id, job_id=job_id, request=payload, trace_id=trace_id)
