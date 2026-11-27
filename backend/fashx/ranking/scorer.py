"""Deterministic weighted ranking scorer and tie-breaking (Task 8.4.13)."""

from __future__ import annotations

from dataclasses import dataclass

from fashx.ranking.config import FeatureWeights


@dataclass(frozen=True)
class FeatureValues:
    """Feature inputs accepted by the deterministic weighted scorer."""

    category: float | None
    style: float | None
    color: float | None
    price: float | None
    availability: float | None
    size: float | None
    visual: float | None
    feedback: float | None
    quality: float | None


@dataclass(frozen=True)
class ScoreResult:
    """Normalized [0, 100] score and per-feature contribution breakdown."""

    score: float
    contributions: dict[str, float]


def validate_score(value: float | None) -> bool:
    """Return True iff value is a valid normalized feature score in [0.0, 1.0]."""
    return value is not None and 0.0 <= value <= 1.0


def calculate_score(
    features: FeatureValues,
    weights: FeatureWeights = FeatureWeights(),
) -> ScoreResult:
    """Calculate normalized deterministic ranking score in [0, 100].

    Missing optional features (``None``) are excluded from the weight
    denominator so missing signals never unfairly penalize candidates.
    """
    configured = {
        "category": weights.category,
        "style": weights.style,
        "color": weights.color,
        "price": weights.price,
        "availability": weights.availability,
        "size": weights.size,
        "visual": weights.visual,
        "feedback": weights.feedback,
        "quality": weights.quality,
    }
    values = {
        "category": features.category,
        "style": features.style,
        "color": features.color,
        "price": features.price,
        "availability": features.availability,
        "size": features.size,
        "visual": features.visual,
        "feedback": features.feedback,
        "quality": features.quality,
    }

    total_weight = 0.0
    contributions: dict[str, float] = {}
    for name, weight in configured.items():
        if weight < 0:
            raise ValueError("Feature weights cannot be negative")
        value = values[name]
        if weight == 0 or value is None:
            continue
        if not validate_score(value):
            raise ValueError(f"Invalid feature score: {name}")
        contributions[name] = weight * value
        total_weight += weight

    if total_weight <= 0:
        raise ValueError("No applicable ranking features")

    final_score = (sum(contributions.values()) / total_weight) * 100.0
    return ScoreResult(
        score=round(final_score, 4),
        contributions=contributions,
    )


def ranking_sort_key(item: object) -> tuple[float, float, float, float, str]:
    """Stable deterministic tie-breaking key across ranked items."""
    return (
        -float(item.score),
        -float(item.category_score),
        -float(item.availability_freshness),
        -float(item.quality_score),
        str(item.product_id),
    )
