from __future__ import annotations

from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class FitOutcome(str, Enum):
    """Explicit deterministic fit recommendation outcomes."""

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
    """Consented shopper body measurements."""

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
    """Product catalog metadata for fit assessment."""

    model_config = ConfigDict(extra="forbid")

    product_id: str
    merchant_id: str
    merchant_offer_id: str
    category: str
    available_sizes: list[str] = Field(default_factory=list)


class FitModelSpec(BaseModel):
    """Validated category-specific fit recommendation model."""

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
    """Evidence-backed fit recommendation response."""

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
