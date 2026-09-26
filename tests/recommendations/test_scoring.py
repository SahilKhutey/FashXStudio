from decimal import Decimal
from uuid import uuid4

from app.domain.recommendations.entities import RecommendationCandidate
from app.domain.recommendations.ranking import calculate_score
from app.domain.recommendations.recommendation_context import (
    RecommendationContext,
)
from app.domain.recommendations.scoring import (
    context_score,
    match,
    price_match,
)


def test_calculate_score():
    score = calculate_score(
        personalization=Decimal("1"),
        context=Decimal("1"),
        price=Decimal("1"),
        region=Decimal("1"),
        source=Decimal("1"),
    )
    assert score == Decimal("1")


def test_score_is_bounded():
    score = calculate_score(
        personalization=Decimal("5"),
        context=Decimal("5"),
        price=Decimal("5"),
        region=Decimal("5"),
        source=Decimal("5"),
    )
    assert score == Decimal("1")

    negative_score = calculate_score(
        personalization=Decimal("-2"),
        context=Decimal("-2"),
        price=Decimal("-2"),
        region=Decimal("-2"),
        source=Decimal("-2"),
    )
    assert negative_score == Decimal("0")


def test_match_helper():
    assert match("Sneakers", "sneakers") == Decimal("1")
    assert match("Sneakers", "Boots") == Decimal("0")
    assert match(None, "sneakers") == Decimal("0")
    assert match("Sneakers", None) == Decimal("0")


def test_price_match_helper():
    candidate = RecommendationCandidate(
        product_id=uuid4(),
        title="Jacket",
        price=Decimal("2500"),
    )
    ctx_in_range = RecommendationContext(
        min_price=Decimal("1000"),
        max_price=Decimal("3000"),
    )
    assert price_match(candidate, ctx_in_range) == Decimal("1")

    ctx_too_expensive = RecommendationContext(
        max_price=Decimal("2000"),
    )
    assert price_match(candidate, ctx_too_expensive) == Decimal("0")

    ctx_too_cheap = RecommendationContext(
        min_price=Decimal("3000"),
    )
    assert price_match(candidate, ctx_too_cheap) == Decimal("0")


def test_context_score_dimensions():
    candidate = RecommendationCandidate(
        product_id=uuid4(),
        title="Dress",
        category="dresses",
        brand="Zara",
        style="chic",
    )
    ctx_full_match = RecommendationContext(
        category="dresses",
        brand="Zara",
        style="chic",
    )
    score = context_score(candidate, ctx_full_match)
    assert score == Decimal("1")

    ctx_no_match = RecommendationContext(
        category="jackets",
        brand="Nike",
    )
    assert context_score(candidate, ctx_no_match) == Decimal("0")
