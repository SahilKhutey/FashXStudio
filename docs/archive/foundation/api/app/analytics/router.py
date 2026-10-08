from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from api.app.auth.dependencies import current_user_id
from api.app.auth.internal import require_internal_service
from api.app.core.dependencies import db_session
from api.app.analytics.application import AnalyticsService
from api.app.analytics.repository import AnalyticsRepository
from schemas.analytics.validation import AnalyticsEventCreate, AnalyticsEventResponse, ValidationMetrics

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


def analytics_service(session: AsyncSession = Depends(db_session)) -> AnalyticsService:
    return AnalyticsService(session, AnalyticsRepository(session))


@router.post("/session-events", response_model=AnalyticsEventResponse)
async def session_event(
    payload: AnalyticsEventCreate,
    request: Request,
    user_id: UUID = Depends(current_user_id),
    service: AnalyticsService = Depends(analytics_service),
) -> AnalyticsEventResponse:
    trace_raw = getattr(request.state, "trace_id", None)
    trace_id = UUID(trace_raw) if trace_raw else None
    return await service.record_session_event(user_id=user_id, request=payload, trace_id=trace_id)


@router.get("/validation", response_model=ValidationMetrics, dependencies=[Depends(require_internal_service)])
async def validation_metrics(
    start_at: datetime | None = Query(default=None),
    end_at: datetime | None = Query(default=None),
    service: AnalyticsService = Depends(analytics_service),
) -> ValidationMetrics:
    now = datetime.now(timezone.utc)
    end = end_at or now
    start = start_at or (end - timedelta(days=30))
    return await service.validation_metrics(start_at=start, end_at=end)
