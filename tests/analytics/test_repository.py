from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from fashx.domain.analytics.entities import (
    AggregationBucket,
    AnalyticsEvent,
)
from fashx.domain.analytics.enums import (
    AggregationPeriod,
    AnalyticsEventType,
)
from fashx.repositories.analytics.memory import (
    InMemoryAnalyticsEventRepository,
    InMemoryAnalyticsMetricRepository,
)


@pytest.mark.asyncio
async def test_save_and_get_event():
    repository = InMemoryAnalyticsEventRepository()

    event = AnalyticsEvent(
        event_type=AnalyticsEventType.PRODUCT_VIEWED,
        session_id="session-1",
    )

    await repository.save(event)

    result = await repository.get(event.id)
    assert result is not None
    assert result.id == event.id
    assert result.event_type == AnalyticsEventType.PRODUCT_VIEWED

    assert await repository.get(uuid4()) is None


@pytest.mark.asyncio
async def test_list_between():
    repository = InMemoryAnalyticsEventRepository()
    now = datetime(2026, 9, 26, 12, 0, tzinfo=UTC)

    e1 = AnalyticsEvent(
        event_type=AnalyticsEventType.PRODUCT_VIEWED,
        session_id="s1",
        occurred_at=now - timedelta(hours=2),
    )
    e2 = AnalyticsEvent(
        event_type=AnalyticsEventType.CART_LINE_ADDED,
        session_id="s1",
        occurred_at=now,
    )
    e3 = AnalyticsEvent(
        event_type=AnalyticsEventType.CHECKOUT_STARTED,
        session_id="s1",
        occurred_at=now + timedelta(hours=2),
    )

    await repository.save(e1)
    await repository.save(e2)
    await repository.save(e3)

    results = await repository.list_between(
        now - timedelta(minutes=30),
        now + timedelta(minutes=30),
    )
    assert len(results) == 1
    assert results[0].id == e2.id


@pytest.mark.asyncio
async def test_metric_repository_save_and_get_bucket():
    repo = InMemoryAnalyticsMetricRepository()
    period_start = datetime(2026, 9, 26, 0, 0, tzinfo=UTC)
    dimensions = {"category": "footwear", "region": "IN"}

    bucket = AggregationBucket(
        metric_name="product_views",
        period=AggregationPeriod.DAY,
        period_start=period_start,
        dimensions=dimensions,
        count=15,
    )

    await repo.save_bucket(bucket)

    retrieved = await repo.get_bucket(
        metric_name="product_views",
        period_start=period_start,
        dimensions=dimensions,
    )
    assert retrieved is not None
    assert retrieved.count == 15
    assert retrieved.metric_name == "product_views"

    missing = await repo.get_bucket(
        metric_name="product_views",
        period_start=period_start,
        dimensions={"region": "US"},
    )
    assert missing is None
