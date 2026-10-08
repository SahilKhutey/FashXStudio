from decimal import Decimal
from uuid import uuid4

import pytest

from fashx.core.event_bus import EventBus
from fashx.domain.recommendations.entities import (
    RecommendationCandidate,
)
from fashx.domain.recommendations.events import RecommendationsGenerated
from fashx.domain.recommendations.recommendation_context import (
    RecommendationContext,
)
from fashx.domain.recommendations.service import (
    RecommendationService,
)
from fashx.repositories.recommendations.memory import (
    InMemoryRecommendationCandidateRepository,
)


class FakePersonalizationProvider:
    async def score(
        self,
        customer_id,
        **kwargs,
    ):
        return Decimal("0.80")


@pytest.mark.asyncio
async def test_recommendation_service():
    repository = InMemoryRecommendationCandidateRepository()
    product_id = uuid4()

    await repository.add(
        RecommendationCandidate(
            product_id=product_id,
            title="Black Streetwear Jacket",
            category="jackets",
            style="streetwear",
            color="black",
            price=Decimal("2499"),
        )
    )

    service = RecommendationService(
        candidate_repository=repository,
        personalization_provider=FakePersonalizationProvider(),
    )

    result = await service.recommend(
        context=RecommendationContext(
            customer_id=uuid4(),
            category="jackets",
            style="streetwear",
            max_price=Decimal("5000"),
        )
    )

    assert len(result.items) == 1
    assert result.items[0].product_id == product_id
    assert result.items[0].rank == 1
    assert len(result.items[0].explanations) >= 1


@pytest.mark.asyncio
async def test_anonymous_recommendation():
    repository = InMemoryRecommendationCandidateRepository()
    pid = uuid4()
    await repository.add(
        RecommendationCandidate(
            product_id=pid,
            title="Linen Shirt",
            category="shirts",
            style="casual",
            price=Decimal("1200"),
        )
    )

    service = RecommendationService(
        candidate_repository=repository,
        personalization_provider=FakePersonalizationProvider(),
    )

    result = await service.recommend(
        context=RecommendationContext(
            customer_id=None,
            category="shirts",
            style="casual",
        )
    )

    assert len(result.items) == 1
    assert result.items[0].product_id == pid


@pytest.mark.asyncio
async def test_product_exclusion():
    repository = InMemoryRecommendationCandidateRepository()
    pid1 = uuid4()
    pid2 = uuid4()

    await repository.add(
        RecommendationCandidate(product_id=pid1, title="Excluded Item", category="hats")
    )
    await repository.add(
        RecommendationCandidate(product_id=pid2, title="Kept Item", category="hats")
    )

    service = RecommendationService(
        candidate_repository=repository,
        personalization_provider=FakePersonalizationProvider(),
    )

    result = await service.recommend(
        context=RecommendationContext(
            category="hats",
            exclude_product_ids=(pid1,),
        )
    )

    assert len(result.items) == 1
    assert result.items[0].product_id == pid2


@pytest.mark.asyncio
async def test_event_published_on_recommend():
    events = []
    bus = EventBus()

    async def on_gen(envelope):
        events.append(envelope.event)

    bus.subscribe("RecommendationsGenerated", on_gen)

    repository = InMemoryRecommendationCandidateRepository()
    await repository.add(
        RecommendationCandidate(product_id=uuid4(), title="Scarf", category="accessories")
    )

    service = RecommendationService(
        candidate_repository=repository,
        personalization_provider=FakePersonalizationProvider(),
        event_bus=bus,
    )

    cid = uuid4()
    await service.recommend(
        context=RecommendationContext(customer_id=cid, category="accessories")
    )

    assert len(events) == 1
    assert isinstance(events[0], RecommendationsGenerated)
    assert events[0].customer_id == cid
    assert events[0].result_count == 1
