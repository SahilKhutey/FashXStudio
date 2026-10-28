from datetime import UTC, datetime
from enum import Enum
from typing import Any
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
    ONBOARDING_COMPLETED = "onboarding_completed"
    FEED_VIEWED = "feed_viewed"
    GARMENT_OPENED = "garment_opened"
    GARMENT_SAVED = "garment_saved"
    TRYON_SUBMITTED = "tryon_submitted"
    TRYON_COMPLETED = "tryon_completed"
    TRYON_FAILED = "tryon_failed"
    RETAILER_OPENED = "retailer_opened"
    FEEDBACK_SUBMITTED = "feedback_submitted"


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


def get_analytics_session_factory() -> Any:
    from fashx.core.database import get_session_factory

    return get_session_factory()


@router.post(
    "/session-events",
    response_model=BatchSessionEventsResponse,
    status_code=201,
    dependencies=[Depends(rate_limit(max_requests=120, window_seconds=60, scope="analytics"))],
)
async def record_session_events(
    payload: BatchSessionEventsRequest,
    principal: Principal = Depends(get_principal),
    session_factory: Any = Depends(get_analytics_session_factory),
) -> BatchSessionEventsResponse:
    """Record a batch of client session events and persist them to durable domain storage."""
    from database.models.commerce_feedback import DomainEvent

    user_uuid = None
    if principal and principal.user_id:
        try:
            user_uuid = UUID(str(principal.user_id))
        except (ValueError, TypeError):
            user_uuid = None

    now = datetime.now(UTC)
    async with session_factory() as session:
        for item in payload.events:
            rec = DomainEvent(
                event_type=f"session_{item.event_type.value}",
                schema_version=1,
                user_id=user_uuid,
                object_type="garment" if item.garment_id else None,
                object_id=item.garment_id,
                occurred_at=item.timestamp or now,
                payload={
                    "session_id": item.session_id,
                    "event_type": item.event_type.value,
                    "garment_id": str(item.garment_id) if item.garment_id else None,
                },
            )
            session.add(rec)
        await session.commit()

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
