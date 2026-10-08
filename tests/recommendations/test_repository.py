from uuid import uuid4

import pytest

from fashx.domain.recommendations.entities import (
    RecommendationCandidate,
)
from fashx.repositories.recommendations.memory import (
    InMemoryRecommendationCandidateRepository,
)


@pytest.mark.asyncio
async def test_repository_category_filter():
    repository = InMemoryRecommendationCandidateRepository()
    candidate = RecommendationCandidate(
        product_id=uuid4(),
        title="Jacket",
        category="jackets",
    )
    await repository.add(candidate)

    result = await repository.list_candidates(category="jackets")
    assert len(result) == 1
    assert result[0].title == "Jacket"

    empty_result = await repository.list_candidates(category="shoes")
    assert len(empty_result) == 0


@pytest.mark.asyncio
async def test_repository_brand_and_region_filter():
    repository = InMemoryRecommendationCandidateRepository()
    cand1 = RecommendationCandidate(
        product_id=uuid4(),
        title="Global Nike Sneaker",
        brand="Nike",
        region=None,
    )
    cand2 = RecommendationCandidate(
        product_id=uuid4(),
        title="IN Exclusive Nike Sneaker",
        brand="Nike",
        region="IN",
    )
    cand3 = RecommendationCandidate(
        product_id=uuid4(),
        title="US Exclusive Adidas",
        brand="Adidas",
        region="US",
    )
    await repository.add(cand1)
    await repository.add(cand2)
    await repository.add(cand3)

    # In India: should get Global Nike Sneaker and IN Exclusive Nike Sneaker
    in_nike = await repository.list_candidates(brand="Nike", region="IN")
    assert len(in_nike) == 2

    # In US: should get Adidas
    us_adidas = await repository.list_candidates(brand="Adidas", region="US")
    assert len(us_adidas) == 1
    assert us_adidas[0].title == "US Exclusive Adidas"
