from decimal import Decimal
from uuid import uuid4

import pytest

from app.core.context import CoreContext
from app.core.errors import ConflictError, NotFoundError
from app.core.event_bus import EventBus
from fashx.domain.trends.entities import Trend, TrendObservation
from fashx.domain.trends.enums import TrendStatus, TrendType
from fashx.domain.trends.events import (
    TrendActivated,
    TrendCreated,
    TrendObservationCreated,
)
from fashx.domain.trends.provider import TestTrendProvider
from fashx.domain.trends.service import TrendService
from fashx.repositories.trends.memory import (
    InMemoryTrendObservationRepository,
    InMemoryTrendRepository,
)


@pytest.mark.asyncio
async def test_create_observation():
    bus = EventBus()
    events = []

    async def on_event(envelope):
        events.append(envelope.event)

    bus.subscribe("TrendObservationCreated", on_event)

    service = TrendService(
        trend_repository=InMemoryTrendRepository(),
        observation_repository=InMemoryTrendObservationRepository(),
        event_bus=bus,
    )

    observation = TrendObservation(
        topic="cargo pants",
        value=Decimal("100"),
    )

    result = await service.create_observation(
        context=CoreContext.create(),
        observation=observation,
    )

    assert result.id == observation.id
    assert len(events) == 1
    assert isinstance(events[0], TrendObservationCreated)
    assert events[0].entity_id == observation.id
    assert events[0].topic == "cargo pants"


@pytest.mark.asyncio
async def test_create_trend():
    bus = EventBus()
    events = []

    async def on_event(envelope):
        events.append(envelope.event)

    bus.subscribe("TrendCreated", on_event)

    service = TrendService(
        trend_repository=InMemoryTrendRepository(),
        observation_repository=InMemoryTrendObservationRepository(),
        event_bus=bus,
    )

    trend = Trend(
        topic="boho chic",
        strength=0.75,
        confidence=0.8,
        momentum=0.15,
    )

    result = await service.create_trend(
        context=CoreContext.create(),
        trend=trend,
    )

    assert result.id == trend.id
    assert len(events) == 1
    assert isinstance(events[0], TrendCreated)
    assert events[0].entity_id == trend.id
    assert events[0].topic == "boho chic"


@pytest.mark.asyncio
async def test_get_trend():
    service = TrendService(
        trend_repository=InMemoryTrendRepository(),
        observation_repository=InMemoryTrendObservationRepository(),
    )

    trend = Trend(topic="athleisure")
    await service.create_trend(trend=trend)

    retrieved = await service.get_trend(trend.id)
    assert retrieved.id == trend.id
    assert retrieved.topic == "athleisure"

    with pytest.raises(NotFoundError, match="Trend not found"):
        await service.get_trend(uuid4())


@pytest.mark.asyncio
async def test_list_trends():
    service = TrendService(
        trend_repository=InMemoryTrendRepository(),
        observation_repository=InMemoryTrendObservationRepository(),
    )

    t1 = Trend(
        topic="active 1",
        status=TrendStatus.ACTIVE,
        trend_type=TrendType.STYLE,
        region="IN",
    )
    t2 = Trend(
        topic="draft 1",
        status=TrendStatus.DRAFT,
        trend_type=TrendType.STYLE,
    )
    await service.create_trend(trend=t1)
    await service.create_trend(trend=t2)

    active_list = await service.list_trends(region="IN", trend_type="style")
    assert len(active_list) == 1
    assert active_list[0].topic == "active 1"


@pytest.mark.asyncio
async def test_activate_trend_lifecycle():
    bus = EventBus()
    events = []

    async def on_event(envelope):
        events.append(envelope.event)

    bus.subscribe("TrendActivated", on_event)

    service = TrendService(
        trend_repository=InMemoryTrendRepository(),
        observation_repository=InMemoryTrendObservationRepository(),
        event_bus=bus,
    )

    trend = Trend(topic="monochrome", status=TrendStatus.DRAFT)
    await service.create_trend(trend=trend)

    activated = await service.activate_trend(trend.id)
    assert activated.status == TrendStatus.ACTIVE
    assert activated.version == 2
    assert len(events) == 1
    assert isinstance(events[0], TrendActivated)
    assert events[0].entity_id == trend.id


@pytest.mark.asyncio
async def test_invalid_lifecycle_transition():
    service = TrendService(
        trend_repository=InMemoryTrendRepository(),
        observation_repository=InMemoryTrendObservationRepository(),
    )

    trend = Trend(topic="old trend", status=TrendStatus.ARCHIVED)
    await service.create_trend(trend=trend)

    # ARCHIVED cannot transition to ACTIVE
    with pytest.raises(ConflictError, match="Invalid trend transition"):
        await service.activate_trend(trend.id)


@pytest.mark.asyncio
async def test_test_trend_provider():
    provider = TestTrendProvider()
    data = await provider.collect(region="IN")
    assert len(data) >= 2
    assert data[0].region == "IN"
    assert data[0].topic == "oversized jacket"
