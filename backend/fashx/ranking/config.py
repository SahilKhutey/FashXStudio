"""Versioned ranking configuration and weights for Phase 08.4."""

from __future__ import annotations

from dataclasses import dataclass

from pydantic import BaseModel


@dataclass(frozen=True)
class FeatureWeights:
    """Normalized feature weight configuration."""

    category: float = 0.20
    style: float = 0.15
    color: float = 0.10
    price: float = 0.10
    availability: float = 0.10
    size: float = 0.10
    visual: float = 0.10
    feedback: float = 0.10
    quality: float = 0.05


BASELINE_WEIGHTS = FeatureWeights(
    category=0.45,
    style=0.0,
    color=0.0,
    price=0.10,
    availability=0.25,
    size=0.0,
    visual=0.0,
    feedback=0.0,
    quality=0.20,
)

PERSONALIZED_WEIGHTS = FeatureWeights()


@dataclass(frozen=True)
class RankingConfig:
    """Immutable versioned ranking configuration."""

    ranking_version: str
    config_version: str
    taxonomy_version: str
    weights: FeatureWeights
    min_attribute_confidence: float = 0.70
    max_availability_age_seconds: int = 86400
    visual_similarity_lower_bound: float = 0.0
    visual_similarity_upper_bound: float = 1.0
    cache_ttl_seconds: int = 60


RANKING_CONFIGS: dict[str, RankingConfig] = {
    "personalized-v1": RankingConfig(
        ranking_version="personalized-v1",
        config_version="cfg-personalized-v1",
        taxonomy_version="v1.0.0",
        weights=PERSONALIZED_WEIGHTS,
    ),
    "baseline-v1": RankingConfig(
        ranking_version="baseline-v1",
        config_version="cfg-baseline-v1",
        taxonomy_version="v1.0.0",
        weights=BASELINE_WEIGHTS,
    ),
}


def get_ranking_config(ranking_version: str) -> RankingConfig:
    """Resolve a supported ranking configuration or raise ValueError."""
    cfg = RANKING_CONFIGS.get(ranking_version)
    if cfg is None:
        supported = ", ".join(sorted(RANKING_CONFIGS))
        raise ValueError(
            f"Unsupported ranking_version '{ranking_version}'. Supported: {supported}"
        )
    return cfg


class RankingConfigResponse(BaseModel):
    """Publicly inspectable ranking configuration metadata."""

    ranking_version: str
    config_version: str
    taxonomy_version: str
    supported_versions: list[str]
    weights: dict[str, float]
    max_availability_age_seconds: int
    cache_ttl_seconds: int
