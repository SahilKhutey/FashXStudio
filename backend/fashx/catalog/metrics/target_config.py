from __future__ import annotations

from database.models.catalog import CatalogSource
from fashx.catalog.metrics.contracts import (
    PilotTargetLimits,
    QualityTargetLimits,
    SamplingConfig,
    TargetConfig,
)

DEFAULT_TARGET_CONFIG = TargetConfig(
    version="1.0",
    pilot=PilotTargetLimits(
        minimum_live_authorized_sources=1,
        minimum_usable_offers=1000,
        expansion_minimum_offers=2000,
        expansion_maximum_offers=5000,
    ),
    quality=QualityTargetLimits(
        minimum_fresh_price_percentage=95.0,
        maximum_broken_link_percentage_exclusive=1.0,
        maximum_unauthorized_sources=0,
        minimum_image_permission_traceability_percentage=100.0,
    ),
    sampling=SamplingConfig(
        method="stratified_random",
        require_reproducible_seed=True,
        default_seed=42,
        default_sample_size=100,
    ),
)


def get_target_config(version: str = "1.0") -> TargetConfig:
    """Retrieve versioned target configuration."""
    if version == "1.0":
        return DEFAULT_TARGET_CONFIG
    return DEFAULT_TARGET_CONFIG


def get_source_freshness_window_hours(source: CatalogSource | None) -> int:
    """Retrieve the agreed freshness window in hours for a specific catalog source."""
    if source is not None and getattr(source, "freshness_policy_hours", None):
        return int(source.freshness_policy_hours)
    return 24
