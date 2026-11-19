from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class LinkHealthClassification(StrEnum):
    VALID = "VALID"
    UNAVAILABLE = "UNAVAILABLE"
    BROKEN = "BROKEN"
    BROKEN_OR_REMOVED = "BROKEN_OR_REMOVED"
    TEMPORARY_FAILURE = "TEMPORARY_FAILURE"
    INVALID_REDIRECT = "INVALID_REDIRECT"
    UNVERIFIED = "UNVERIFIED"


class CatalogMetricResult(BaseModel):
    """Normalized result for a single catalog target or release gate metric."""

    model_config = ConfigDict(from_attributes=True)

    metric_id: str
    target_value: float
    actual_value: float
    unit: str
    passed: bool
    measured_at: datetime
    numerator: int | None = None
    denominator: int | None = None
    sample_size: int | None = None
    source_ids: list[str] = Field(default_factory=list)
    evaluation_version: str = "1.0"
    evidence_reference: str | None = None
    notes: list[str] = Field(default_factory=list)


class PilotTargetLimits(BaseModel):
    minimum_live_authorized_sources: int = 1
    minimum_usable_offers: int = 1000
    expansion_minimum_offers: int = 2000
    expansion_maximum_offers: int = 5000


class QualityTargetLimits(BaseModel):
    minimum_fresh_price_percentage: float = 95.0
    maximum_broken_link_percentage_exclusive: float = 1.0
    maximum_unauthorized_sources: int = 0
    minimum_image_permission_traceability_percentage: float = 100.0


class SamplingConfig(BaseModel):
    method: str = "stratified_random"
    require_reproducible_seed: bool = True
    default_seed: int = 42
    default_sample_size: int = 100


class TargetConfig(BaseModel):
    version: str = "1.0"
    pilot: PilotTargetLimits = Field(default_factory=PilotTargetLimits)
    quality: QualityTargetLimits = Field(default_factory=QualityTargetLimits)
    sampling: SamplingConfig = Field(default_factory=SamplingConfig)


class LinkCheckResult(BaseModel):
    url: str
    status: LinkHealthClassification
    http_status: int | None = None
    response_time_ms: int | None = None
    error_message: str | None = None
    redirect_url: str | None = None


class UsableProductCheckResult(BaseModel):
    usable_offers_count: int = 0
    canonical_garments_count: int = 0
    product_variants_count: int = 0
    excluded_duplicates_count: int = 0
    excluded_quarantined_count: int = 0
    excluded_inactive_count: int = 0
    excluded_unauthorized_source_count: int = 0
    passed_all: bool = False


class EvaluationReport(BaseModel):
    evaluation_id: UUID
    configuration_version: str
    status: str
    started_at: datetime
    completed_at: datetime | None = None
    all_passed: bool
    metric_results: dict[str, CatalogMetricResult]
    usable_product_breakdown: UsableProductCheckResult
    release_decision: str  # ACCEPT | HOLD
    blockers: list[str] = Field(default_factory=list)
    evidence_references: list[str] = Field(default_factory=list)
