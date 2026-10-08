from decimal import Decimal

from .entities import (
    RecommendationCandidate,
)
from .recommendation_context import (
    RecommendationContext,
)


def match(
    candidate_value: str | None,
    context_value: str | None,
) -> Decimal:
    if not candidate_value or not context_value:
        return Decimal("0")

    if candidate_value.strip().lower() == context_value.strip().lower():
        return Decimal("1")

    return Decimal("0")


def price_match(
    candidate: RecommendationCandidate,
    context: RecommendationContext,
) -> Decimal:
    if candidate.price is None:
        return Decimal("0")

    if context.min_price is not None and candidate.price < context.min_price:
        return Decimal("0")

    if context.max_price is not None and candidate.price > context.max_price:
        return Decimal("0")

    return Decimal("1")


def context_score(
    candidate: RecommendationCandidate,
    context: RecommendationContext,
) -> Decimal:
    dimensions = [
        match(candidate.category, context.category),
        match(candidate.brand, context.brand),
        match(candidate.style, context.style),
        match(candidate.color, context.color),
        match(candidate.material, context.material),
        match(candidate.occasion, context.occasion),
    ]

    active = [score for score in dimensions if score > Decimal("0")]

    if not active:
        return Decimal("0")

    return sum(active) / Decimal(len(active))
