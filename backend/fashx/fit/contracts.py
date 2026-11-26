"""Strict Pydantic v2 contracts for Fit Recommendation Engine (Phase 07.8 + Phase 08.3)."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from enum import Enum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from fashx.fit.enums import (
    ConfidenceType,
    FeedbackReviewStatus,
    FitFeedbackReason,
    FitPreference,
    FitReasonCode,
    MeasurementBasis,
    MissingDataCode,
    PurchaseStatus,
    RecommendationStatus,
)

# ---------------------------------------------------------------------------
# Phase 07.8 Compatibility Contracts (must remain backwards-compatible)
# ---------------------------------------------------------------------------


class FitOutcome(str, Enum):
    """Explicit deterministic fit recommendation outcomes (Phase 07.8)."""

    RECOMMENDED = "RECOMMENDED"
    POSSIBLE_ALTERNATIVES = "POSSIBLE_ALTERNATIVES"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    UNSUPPORTED_CATEGORY = "UNSUPPORTED_CATEGORY"
    STALE_SIZE_CHART = "STALE_SIZE_CHART"
    CONFLICTING_DATA = "CONFLICTING_DATA"
    NO_AVAILABLE_SIZE = "NO_AVAILABLE_SIZE"


class EvidenceReference(BaseModel):
    """Audit provenance linking a fit recommendation to verified input data."""

    model_config = ConfigDict(extra="forbid")

    source_type: str = Field(
        ...,
        description="Type of evidence: SHOPPER_MEASUREMENT, MERCHANT_SIZE_CHART, FIT_MODEL_CONFIG",
    )
    source_id: str = Field(..., description="Durable database or catalog identifier")
    source_revision: str = Field(..., description="Specific revision or version hash of the source data")


class ShopperMeasurementsInput(BaseModel):
    """Consented shopper body measurements (Phase 07.8)."""

    model_config = ConfigDict(extra="forbid")

    user_id: str
    chest_cm: Decimal | None = Field(default=None, gt=0)
    waist_cm: Decimal | None = Field(default=None, gt=0)
    hip_cm: Decimal | None = Field(default=None, gt=0)
    shoulder_cm: Decimal | None = Field(default=None, gt=0)
    length_cm: Decimal | None = Field(default=None, gt=0)
    height_cm: Decimal | None = Field(default=None, gt=0)
    weight_kg: Decimal | None = Field(default=None, gt=0)
    provenance: str = Field(default="shopper_provided")
    measurement_revision: str = Field(default="v1")
    consent_verified: bool = True


class FitProductInput(BaseModel):
    """Product catalog metadata for fit assessment (Phase 07.8)."""

    model_config = ConfigDict(extra="forbid")

    product_id: str
    merchant_id: str
    merchant_offer_id: str
    category: str
    available_sizes: list[str] = Field(default_factory=list)


class FitModelSpec(BaseModel):
    """Validated category-specific fit recommendation model (Phase 07.8)."""

    model_config = ConfigDict(extra="forbid")

    model_id: str = "fashx-fit-rule-engine"
    version: str = "v1.0.0"
    supported_categories: list[str] = Field(
        default_factory=lambda: [
            "shirts",
            "tshirts",
            "casual_shirts",
            "formal_shirts",
            "kurtas",
            "tops",
            "trousers",
            "jeans",
        ]
    )


class FitRecommendationResponse(BaseModel):
    """Evidence-backed fit recommendation response (Phase 07.8)."""

    model_config = ConfigDict(extra="forbid")

    recommendation_id: str
    product_id: str
    merchant_offer_id: str
    outcome: FitOutcome
    recommended_size: str | None = None
    alternative_sizes: list[str] = Field(default_factory=list)
    explanation_code: str
    explanation_message: str
    fit_model_version: str
    evidence: list[EvidenceReference] = Field(default_factory=list)
    fit_guaranteed: bool = False
    disclaimer: str = (
        "Fit guidance is estimated from verified merchant size charts and shopper measurements. "
        "It is not a guarantee of fit."
    )


# ---------------------------------------------------------------------------
# Phase 08.3 Evidence-Based Fit Recommendation Contracts
# ---------------------------------------------------------------------------

FIT_ALGORITHM_VERSION = "08.3.1"
STANDARD_DISCLAIMER_CODE = "SIZE_GUIDANCE_NOT_FIT_GUARANTEE"
STANDARD_DISCLAIMER_TEXT = (
    "This is size guidance based on available product and shopper information. "
    "It does not guarantee physical fit, comfort or appearance."
)


def _require_tz_aware(dt: datetime) -> datetime:
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError("Timestamp must be timezone-aware (UTC recommended)")
    return dt.astimezone(UTC)


class MeasurementValue(BaseModel):
    """Normalized shopper body measurement paired with original entry metadata and revision."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    field: str = Field(..., min_length=1, max_length=32)
    value_cm: Decimal = Field(gt=0)
    original_value: Decimal | None = Field(default=None, gt=0)
    original_unit: str = Field(default="CM", min_length=1, max_length=16)
    measured_at: datetime
    revision: int = Field(ge=1)
    provenance: Literal["SHOPPER_ENTERED", "VERIFIED_SOURCE"] = "SHOPPER_ENTERED"
    status: str = Field(default="ACTIVE", max_length=32)

    @field_validator("field")
    @classmethod
    def _norm_field(cls, v: str) -> str:
        s = v.strip().upper()
        if not s:
            raise ValueError("Measurement field cannot be empty")
        return s

    @field_validator("measured_at")
    @classmethod
    def _tz_measured_at(cls, v: datetime) -> datetime:
        return _require_tz_aware(v)

    @model_validator(mode="after")
    def _default_original(self) -> MeasurementValue:
        if self.original_value is None:
            object.__setattr__(self, "original_value", self.value_cm)
        return self


class SizeRange(BaseModel):
    """Measurement bound (or exact point when minimum_cm == maximum_cm) for one chart field."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    field: str = Field(..., min_length=1, max_length=32)
    minimum_cm: Decimal = Field(gt=0)
    maximum_cm: Decimal = Field(gt=0)
    original_unit: str = Field(default="CM", max_length=16)
    basis: MeasurementBasis = MeasurementBasis.BODY

    @field_validator("field")
    @classmethod
    def _norm_field(cls, v: str) -> str:
        s = v.strip().upper()
        if not s:
            raise ValueError("SizeRange field cannot be empty")
        return s

    def valid_range(self) -> bool:
        """Return True iff lower bound does not exceed upper bound."""
        return self.minimum_cm <= self.maximum_cm


class MerchantSizeOption(BaseModel):
    """A single merchant variant/size row evaluated against a category fit policy."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    variant_id: str = Field(..., min_length=1, max_length=128)
    merchant_size_label: str = Field(..., min_length=1, max_length=64)
    available: bool = True
    availability_status: str = Field(default="IN_STOCK", max_length=32)
    measurements: list[SizeRange] = Field(default_factory=list)


class RecommendedSizeDetail(BaseModel):
    """Selected size option identified strictly by merchant variant ID and merchant label."""

    model_config = ConfigDict(extra="forbid")

    variant_id: str
    merchant_size_label: str


class ConfidenceSummary(BaseModel):
    """Internal evidence score — display_to_shopper remains False until calibrated."""

    model_config = ConfigDict(extra="forbid")

    score: Decimal = Field(ge=0, le=1)
    type: ConfidenceType = ConfidenceType.INTERNAL_EVIDENCE_SCORE
    display_to_shopper: bool = False


class FitEvidenceItem(BaseModel):
    """Single item in the transparent 'Evidence used' breakdown shown to the shopper."""

    model_config = ConfigDict(extra="forbid")

    label: str
    status: str


class FitEvidenceSummary(BaseModel):
    """Full audit & provenance envelope attached to every recommendation snapshot."""

    model_config = ConfigDict(extra="forbid")

    merchant_id: str | None = None
    merchant_product_id: str | None = None
    merchant_offer_id: str | None = None
    product_id: str
    size_chart_id: str | None = None
    size_chart_revision: int | None = None
    size_system_code: str | None = None
    measurement_basis: MeasurementBasis = MeasurementBasis.UNKNOWN
    shopper_measurement_revision: int | None = None
    category_policy_version: str | None = None
    fit_algorithm_version: str = FIT_ALGORITHM_VERSION
    fit_preference_revision: int | None = None
    fit_preference_applied: FitPreference | None = None
    preference_evaluated: bool = False
    source_id: str | None = None
    source_revision: str | None = None
    source_permission_revision: int | None = None
    taxonomy_version: str = "1.0"
    evidence_items: list[FitEvidenceItem] = Field(default_factory=list)


class FitRecommendationRequest(BaseModel):
    """Shopper API request — client MUST NOT pass trusted measurements, chart, or confidence."""

    model_config = ConfigDict(extra="forbid")

    product_id: UUID | str
    merchant_offer_id: UUID | str | None = None
    variant_id: str | None = Field(default=None, max_length=128)
    category: str | None = Field(default=None, max_length=64)


class FitRecommendationResult(BaseModel):
    """Phase 08.3 API and domain output for fit evaluation or explicit abstention."""

    model_config = ConfigDict(extra="forbid")

    recommendation_id: str
    status: RecommendationStatus
    recommended_size: RecommendedSizeDetail | None = None
    alternative_sizes: list[RecommendedSizeDetail] = Field(default_factory=list)
    confidence: ConfidenceSummary
    reason_codes: list[FitReasonCode | str] = Field(default_factory=list)
    missing_information: list[MissingDataCode | str] = Field(default_factory=list)
    explanations: list[str] = Field(default_factory=list)
    explanation: str
    evidence: FitEvidenceSummary
    is_valid: bool = True
    invalidated_reason: str | None = None
    fit_guaranteed: bool = False
    disclaimer_code: str = STANDARD_DISCLAIMER_CODE
    disclaimer: str = STANDARD_DISCLAIMER_TEXT
    next_actions: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    expires_at: datetime | None = None


class FitFeedbackCreateRequest(BaseModel):
    """Shopper feedback submission — backend derives product, merchant, and chart revisions."""

    model_config = ConfigDict(extra="forbid")

    reason: FitFeedbackReason
    purchase_status: PurchaseStatus = PurchaseStatus.UNKNOWN
    tried_on: bool = False
    kept_item: bool | None = None
    selected_different_size: bool = False
    comment: str | None = Field(default=None, max_length=1000)


class FitFeedbackResponse(BaseModel):
    """Persisted feedback summary tied to a recommendation snapshot."""

    model_config = ConfigDict(extra="forbid")

    feedback_id: str
    recommendation_id: str
    product_id: str
    merchant_id: str | None = None
    size_chart_id: str | None = None
    size_chart_revision: int | None = None
    recommended_size: str | None = None
    reason: FitFeedbackReason
    purchase_status: PurchaseStatus
    tried_on: bool
    kept_item: bool | None = None
    selected_different_size: bool
    feedback_basis: str
    review_status: FeedbackReviewStatus
    comment: str | None = None
    created_at: datetime


class FitFeedbackReviewRequest(BaseModel):
    """Authorized reviewer triage payload — never mutates fit rules automatically."""

    model_config = ConfigDict(extra="forbid")

    review_status: FeedbackReviewStatus
    classified_issue: str | None = Field(default=None, max_length=128)
    promote_to_evaluation: bool = False
