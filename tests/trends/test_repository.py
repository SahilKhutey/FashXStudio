from decimal import Decimal
from uuid import uuid4

import pytest

from app.domain.trends.entities import Trend, TrendObservation
from app.domain.trends.enums import TrendStatus, TrendType
from fashx.repositories.trends.memory import (
    InMemoryTrendObservationRepository,
    InMemoryTrendRepository,
)


@pytest.mark.asyncio
async def test_active_trend_lookup():
    repository = InMemoryTrendRepository()
    trend = Trend(
        topic="streetwear",
        status=TrendStatus.ACTIVE,
    )
    await repository.save(trend)

    result = await repository.list_active()
    assert len(result) == 1
    assert result[0].topic == "streetwear"


@pytest.mark.asyncio
async def test_trend_repository_get_and_save():
    repository = InMemoryTrendRepository()
    tid = uuid4()
    trend = Trend(
        id=tid,
        topic="minimalism",
        status=TrendStatus.DRAFT,
    )
    await repository.save(trend)

    retrieved = await repository.get(tid)
    assert retrieved is not None
    assert retrieved.id == tid
    assert retrieved.topic == "minimalism"

    non_existent = await repository.get(uuid4())
    assert non_existent is None


@pytest.mark.asyncio
async def test_trend_repository_filter_by_region():
    repository = InMemoryTrendRepository()
    t1 = Trend(
        topic="t1",
        status=TrendStatus.ACTIVE,
        region="IN",
    )
    t2 = Trend(
        topic="t2",
        status=TrendStatus.ACTIVE,
        region="US",
    )
    t3 = Trend(
        topic="t3",
        status=TrendStatus.ACTIVE,
        region=None,  # Global trends should match
    )
    await repository.save(t1)
    await repository.save(t2)
    await repository.save(t3)

    in_trends = await repository.list_active(region="IN")
    assert len(in_trends) == 2  # t1 and t3 (global)
    topics = {t.topic for t in in_trends}
    assert "t1" in topics
    assert "t3" in topics


@pytest.mark.asyncio
async def test_trend_repository_filter_by_trend_type():
    repository = InMemoryTrendRepository()
    t1 = Trend(
        topic="style trend",
        status=TrendStatus.ACTIVE,
        trend_type=TrendType.STYLE,
    )
    t2 = Trend(
        topic="color trend",
        status=TrendStatus.ACTIVE,
        trend_type=TrendType.COLOR,
    )
    await repository.save(t1)
    await repository.save(t2)

    styles = await repository.list_active(trend_type="style")
    assert len(styles) == 1
    assert styles[0].topic == "style trend"


@pytest.mark.asyncio
async def test_observation_repository_save_and_list():
    repo = InMemoryTrendObservationRepository()
    obs1 = TrendObservation(
        topic="wide-leg denim",
        value=Decimal("150"),
    )
    obs2 = TrendObservation(
        topic="Wide-Leg Denim",
        value=Decimal("200"),
    )
    obs3 = TrendObservation(
        topic="skinny jeans",
        value=Decimal("50"),
    )

    await repo.save(obs1)
    await repo.save(obs2)
    await repo.save(obs3)

    results = await repo.list_by_topic("wide-leg denim")
    assert len(results) == 2
    for r in results:
        assert r.topic.lower() == "wide-leg denim"
