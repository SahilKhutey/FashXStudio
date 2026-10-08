from decimal import Decimal
from uuid import uuid4

import pytest

from app.core.errors import ValidationError
from fashx.domain.recommendations.entities import (
    RecommendationCandidate,
    RecommendationExplanation,
    RecommendationItem,
    RecommendationResult,
)
from fashx.domain.recommendations.enums import RecommendationReason
from fashx.domain.recommendations.recommendation_context import (
    RecommendationContext,
)


def test_candidate_valid():
    candidate = RecommendationCandidate(
        product_id=uuid4(),
        title="Streetwear Jacket",
        price=Decimal("2499.00"),
    )
    candidate.validate()


def test_candidate_requires_title():
    candidate = RecommendationCandidate(
        product_id=uuid4()
    )
    with pytest.raises(ValidationError, match="Recommendation candidate requires title"):
        candidate.validate()


def test_candidate_rejects_negative_price():
    candidate = RecommendationCandidate(
        product_id=uuid4(),
        title="Jacket",
        price=Decimal("-1"),
    )
    with pytest.raises(ValidationError, match="Candidate price cannot be negative"):
        candidate.validate()


def test_candidate_invalid_currency():
    candidate = RecommendationCandidate(
        product_id=uuid4(),
        title="Jacket",
        currency="INVALID",
    )
    with pytest.raises(ValidationError, match="Currency must be a 3-character code"):
        candidate.validate()


def test_context_validation():
    ctx = RecommendationContext(limit=10, min_price=Decimal("100"), max_price=Decimal("500"))
    ctx.validate()

    with pytest.raises(ValidationError, match="Recommendation limit must be at least 1"):
        RecommendationContext(limit=0).validate()

    with pytest.raises(ValidationError, match="Recommendation limit cannot exceed 100"):
        RecommendationContext(limit=101).validate()

    with pytest.raises(ValidationError, match="Minimum price cannot be negative"):
        RecommendationContext(min_price=Decimal("-10")).validate()

    with pytest.raises(ValidationError, match="Maximum price cannot be less than minimum price"):
        RecommendationContext(min_price=Decimal("500"), max_price=Decimal("100")).validate()


def test_recommendation_result_structure():
    pid = uuid4()
    expl = RecommendationExplanation(
        reason=RecommendationReason.STYLE_MATCH,
        score=Decimal("0.85"),
        message="Matches requested style.",
    )
    item = RecommendationItem(
        product_id=pid,
        variant_id=None,
        listing_id=None,
        score=Decimal("0.85"),
        rank=1,
        explanations=(expl,),
    )
    result = RecommendationResult(items=(item,), total_candidates=1)
    assert len(result.items) == 1
    assert result.total_candidates == 1
    assert result.engine_version == "1.0"
