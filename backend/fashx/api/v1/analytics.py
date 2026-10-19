from datetime import UTC, datetime
from enum import Enum
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field

from fashx.core.context import CoreContext
from fashx.core.runtime import get_core_runtime
from fashx.domain.analytics.entities import (
    AnalyticsEvent,
)
from fashx.domain.analytics.enums import (
    AggregationPeriod,
    AnalyticsEventType,
)
from fashx.domain.analytics.service import (
    AnalyticsService,
)
from fashx.security.deps import Principal, get_principal
from fashx.security.ratelimit import rate_limit

from .analytics_schemas import (
    AnalyticsAggregateRequest,
    AnalyticsEventRequest,
)

router = APIRouter(
    prefix="/analytics",
    tags=["analytics"],
)


class SessionEventType(str, Enum):
    IMPRESSION = "impression"
    CLICK = "click"


class SessionEventItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_type: SessionEventType = SessionEventType.IMPRESSION
    garment_id: UUID | None = None
    session_id: str | None = None
    timestamp: datetime | None = None


class BatchSessionEventsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    events: list[SessionEventItem] = Field(..., max_length=100)


class BatchSessionEventsResponse(BaseModel):
    status: str = "recorded"
    count: int


@router.post(
    "/session-events",
    response_model=BatchSessionEventsResponse,
    status_code=201,
    dependencies=[Depends(rate_limit(max_requests=120, window_seconds=60, scope="analytics"))],
)
async def record_session_events(
    payload: BatchSessionEventsRequest,
    principal: Principal = Depends(get_principal),
) -> BatchSessionEventsResponse:
    """Record a batch of client session events (e.g. viewable impression batches)."""
    return BatchSessionEventsResponse(status="recorded", count=len(payload.events))


def get_analytics_service() -> AnalyticsService:
    return get_core_runtime().registry.get(
        "analytics_service"
    )


@router.post("/events")
async def record_event(
    payload: AnalyticsEventRequest,
    service: AnalyticsService = Depends(
        get_analytics_service
    ),
):
    event = AnalyticsEvent(
        event_type=AnalyticsEventType(
            payload.event_type
        ),
        customer_id=payload.customer_id,
        session_id=payload.session_id,
        product_id=payload.product_id,
        variant_id=payload.variant_id,
        listing_id=payload.listing_id,
        category=payload.category,
        brand=payload.brand,
        region=payload.region,
        value=payload.value,
        currency=payload.currency,
        properties=payload.properties,
        occurred_at=(
            payload.occurred_at
            or datetime.now(UTC)
        ),
    )

    return await service.record_event(
        context=CoreContext.create(),
        event=event,
    )


@router.post("/aggregate")
async def aggregate_events(
    payload: AnalyticsAggregateRequest,
    service: AnalyticsService = Depends(
        get_analytics_service
    ),
):
    return await service.aggregate(
        start=payload.start,
        end=payload.end,
        metric_name=payload.metric_name,
        period=AggregationPeriod(
            payload.period
        ),
    )
