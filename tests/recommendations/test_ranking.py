from decimal import Decimal
from uuid import UUID, uuid4

from fashx.domain.recommendations.entities import (
    RecommendationCandidate,
)
from fashx.domain.recommendations.ranking import (
    apply_diversity,
    rank_candidates,
)


def test_rank_candidates():
    first = RecommendationCandidate(
        product_id=uuid4(),
        title="First",
    )
    second = RecommendationCandidate(
        product_id=uuid4(),
        title="Second",
    )
    result = rank_candidates(
        [
            (first, Decimal("0.40")),
            (second, Decimal("0.90")),
        ]
    )
    assert result[0][0] == second
    assert result[1][0] == first


def test_deterministic_tie_breaker():
    id_low = UUID("00000000-0000-0000-0000-000000000001")
    id_high = UUID("ffffffff-ffff-ffff-ffff-ffffffffffff")

    cand1 = RecommendationCandidate(product_id=id_low, title="Low")
    cand2 = RecommendationCandidate(product_id=id_high, title="High")

    # Same score: high UUID string comes first in reverse sort
    result = rank_candidates([(cand1, Decimal("0.50")), (cand2, Decimal("0.50"))])
    assert result[0][0].product_id == id_high
    assert result[1][0].product_id == id_low


def test_diversity_layer_limits_concentration():
    brand_a_items = [
        (RecommendationCandidate(product_id=uuid4(), title=f"BrandA {i}", brand="BrandA"), Decimal("0.90"))
        for i in range(5)
    ]
    brand_b_item = (
        RecommendationCandidate(product_id=uuid4(), title="BrandB 1", brand="BrandB"),
        Decimal("0.85"),
    )
    candidates = brand_a_items + [brand_b_item]

    diversified = apply_diversity(candidates, max_per_brand=2)
    # The first 2 must be BrandA, followed by BrandB, then the overflow of BrandA
    top3_brands = [item[0].brand for item in diversified[:3]]
    assert top3_brands == ["BrandA", "BrandA", "BrandB"]
