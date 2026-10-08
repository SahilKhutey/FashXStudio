from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from app.core.context import CoreContext
from app.core.event_bus import EventBus
from fashx.domain.analytics.entities import AnalyticsEvent
from fashx.domain.analytics.enums import (
    AggregationPeriod,
    AnalyticsEventType,
)
from fashx.domain.analytics.events import (
    AnalyticsEventRecorded,
    AnalyticsMetricAggregated,
)
from fashx.domain.analytics.service import AnalyticsService
from fashx.repositories.analytics.memory import (
    InMemoryAnalyticsEventRepository,
    InMemoryAnalyticsMetricRepository,
)


@pytest.mark.asyncio
async def test_record_event():
    bus = EventBus()
    events = []

    async def on_event(envelope):
        events.append(envelope.event)

    bus.subscribe("AnalyticsEventRecorded", on_event)

    service = AnalyticsService(
        event_repository=InMemoryAnalyticsEventRepository(),
        metric_repository=InMemoryAnalyticsMetricRepository(),
        event_bus=bus,
    )

    event = AnalyticsEvent(
        event_type=AnalyticsEventType.PRODUCT_VIEWED,
        session_id="session-1",
    )

    ctx = CoreContext.create()
    result = await service.record_event(
        context=ctx,
        event=event,
    )

    assert result.id == event.id
    assert result.correlation_id == ctx.correlation_id
    assert len(events) == 1
    assert isinstance(events[0], AnalyticsEventRecorded)
    assert events[0].entity_id == event.id
    assert events[0].event_type == AnalyticsEventType.PRODUCT_VIEWED.value


@pytest.mark.asyncio
async def test_aggregate_product_views():
    events_repo = InMemoryAnalyticsEventRepository()
    metrics_repo = InMemoryAnalyticsMetricRepository()
    bus = EventBus()
    agg_events = []

    async def on_agg(envelope):
        agg_events.append(envelope.event)

    bus.subscribe("AnalyticsMetricAggregated", on_agg)

    service = AnalyticsService(
        event_repository=events_repo,
        metric_repository=metrics_repo,
        event_bus=bus,
    )

    now = datetime(2026, 9, 26, 14, 0, tzinfo=UTC)

    await service.record_event(
        context=CoreContext.create(),
        event=AnalyticsEvent(
            event_type=AnalyticsEventType.PRODUCT_VIEWED,
            session_id="s1",
            region="IN",
            category="footwear",
            occurred_at=now,
            value=Decimal("1999.00"),
        ),
    )

    await service.record_event(
        context=CoreContext.create(),
        event=AnalyticsEvent(
            event_type=AnalyticsEventType.PRODUCT_VIEWED,
            session_id="s2",
            region="IN",
            category="footwear",
            occurred_at=now + timedelta(minutes=15),
            value=Decimal("2499.00"),
        ),
    )

    result = await service.aggregate(
        start=now - timedelta(hours=1),
        end=now + timedelta(hours=1),
        metric_name="product_views",
        period=AggregationPeriod.DAY,
    )

    assert len(result) == 1
    assert result[0].count == 2
    assert result[0].total_value == Decimal("4498.00")
    assert result[0].dimensions["region"] == "IN"
    assert result[0].dimensions["category"] == "footwear"
    assert len(agg_events) == 1
    assert isinstance(agg_events[0], AnalyticsMetricAggregated)
    assert agg_events[0].metric_name == "product_views"
