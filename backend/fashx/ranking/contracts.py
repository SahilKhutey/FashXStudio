"""Versioned request, candidate, feature, and response contracts for Phase 08.4."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from fashx.ranking.enums import (
    AvailabilityStatus,
    FeedbackType,
    PreferencePolarity,
    RankingReasonCode,
    SizeAvailability,
)


class RankingContext(BaseModel):
    """Search and filter context supplied by the shopper."""

    model_config = ConfigDict(extra="forbid")

    query: str | None = None
    category_id: str | None = None
    selected_size: str | None = None
    min_price: Decimal | None = Field(default=None, ge=0)
    max_price: Decimal | None = Field(default=None, ge=0)
    currency: str = Field(default="INR", min_length=3, max_length=3)
    reference_image_asset_id: str | None = None
    reference_product_id: str | None = None
    require_selected_size: bool = False
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=50)

    @model_validator(mode="after")
    def _validate_price_bounds(self) -> RankingContext:
        if (
            self.min_price is not None
            and self.max_price is not None
            and self.min_price > self.max_price
        ):
            raise ValueError("min_price cannot exceed max_price")
        return self


class RankingRequest(BaseModel):
    """Authenticated ranking request; shopper identity comes strictly from auth context."""

    model_config = ConfigDict(extra="forbid")

    context: RankingContext
    ranking_version: str = Field(default="personalized-v1")


class StylePreferenceEntry(BaseModel):
    """Explicit shopper style preference entry."""

    model_config = ConfigDict(extra="forbid")

    style_id: str = Field(min_length=1, max_length=64)
    preference: PreferencePolarity
    strength: float = Field(default=1.0, ge=0.0, le=1.0)


class ShopperRankingPreferencesUpdate(BaseModel):
    """Shopper-editable style, color, category, and budget ranking preferences."""

    model_config = ConfigDict(extra="forbid")

    style_preferences: list[StylePreferenceEntry] | None = None
    preferred_colors: list[str] | None = None
    disliked_colors: list[str] | None = None
    preferred_categories: list[str] | None = None
    budget_min: Decimal | None = Field(default=None, ge=0)
    budget_max: Decimal | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)

    @model_validator(mode="after")
    def _validate_budget(self) -> ShopperRankingPreferencesUpdate:
        if (
            self.budget_min is not None
            and self.budget_max is not None
            and self.budget_min > self.budget_max
        ):
            raise ValueError("budget_min cannot exceed budget_max")
        return self


class ShopperRankingPreferencesResponse(BaseModel):
    """Persisted ranking preferences for the authenticated shopper."""

    style_preferences: list[StylePreferenceEntry]
    preferred_colors: list[str]
    disliked_colors: list[str]
    preferred_categories: list[str]
    budget_min: Decimal | None = None
    budget_max: Decimal | None = None
    currency: str = "INR"
    revision: int = 1


class ProductFeedbackCreate(BaseModel):
    """Explicit shopper product feedback payload."""

    model_config = ConfigDict(extra="forbid")

    feedback_type: FeedbackType
    source: str = Field(default="api", min_length=1, max_length=32)


class ProductFeedbackResponse(BaseModel):
    """Persisted shopper product feedback state."""

    product_id: str
    feedback_type: FeedbackType
    is_active: bool
    created_at: datetime


@dataclass(frozen=True)
class ShopperPreferenceSnapshot:
    """Server-side snapshot of shopper preferences and explicit feedback."""

    shopper_id: str
    profile_revision: int = 1
    liked_styles: dict[str, float] = field(default_factory=dict)
    disliked_styles: dict[str, float] = field(default_factory=dict)
    preferred_colors: frozenset[str] = frozenset()
    disliked_colors: frozenset[str] = frozenset()
    preferred_categories: frozenset[str] = frozenset()
    budget_min: Decimal | None = None
    budget_max: Decimal | None = None
    currency: str = "INR"
    feedback_by_product: dict[str, list[str]] = field(default_factory=dict)
    reference_embedding: tuple[float, ...] | None = None
    reference_embedding_model: str | None = None
    reference_embedding_version: str | None = None
    reference_preprocessing_version: str | None = None
    reference_permission_granted: bool = True


@dataclass(frozen=True)
class CandidateVariant:
    """Merchant-specific variant record for a candidate product."""

    variant_id: str
    size_label: str
    stock_status: str
    is_active: bool = True
    merchant_size_system: str | None = None


@dataclass(frozen=True)
class SourcePermissionSnapshot:
    """Phase 05 source authorization snapshot for eligibility enforcement."""

    can_display_product: bool = True
    can_redirect_to_merchant: bool = True
    can_display_image: bool = True
    permission_expired: bool = False


@dataclass(frozen=True)
class RankingCandidate:
    """Normalized catalog + offer + quality + embedding record entering ranking."""

    product_id: str
    merchant_id: str
    merchant_offer_id: str
    title: str
    category_id: str
    product_status: str = "ACTIVE"
    offer_status: str = "ACTIVE"
    availability_status: str = AvailabilityStatus.IN_STOCK.value
    is_taken_down: bool = False
    is_delisted: bool = False
    is_discontinued: bool = False
    price: Decimal | None = None
    currency: str | None = "INR"
    variants: tuple[CandidateVariant, ...] = ()
    style_tags: dict[str, float] = field(default_factory=dict)
    primary_colors: tuple[str, ...] = ()
    secondary_colors: tuple[str, ...] = ()
    color_confidences: dict[str, float] = field(default_factory=dict)
    image_quality: float | None = None
    attribute_completeness: float | None = None
    data_freshness: float | None = None
    merchant_feed_reliability: float | None = None
    merchant_freshness: float | None = None
    merchant_broken_link_rate: float | None = None
    is_new_merchant: bool = False
    availability_verified_at: datetime | None = None
    availability_freshness: float = 1.0
    embedding: tuple[float, ...] | None = None
    embedding_model: str | None = None
    embedding_version: str | None = None
    preprocessing_version: str | None = None
    permissions: SourcePermissionSnapshot = field(default_factory=SourcePermissionSnapshot)
    is_sponsored: bool = False
    merchant_name: str | None = None
    image_url: str | None = None


@dataclass(frozen=True)
class FeatureProvenance:
    """Traceability record for a single computed ranking feature."""

    feature_name: str
    value: float | None
    source: str


@dataclass(frozen=True)
class RankingFeatures:
    """Normalized [0.0, 1.0] ranking feature vector with optional missing indicators."""

    category_relevance: float
    style_preference: float
    color_preference: float
    price_preference: float
    availability_score: float
    size_availability_score: float | None
    visual_similarity: float | None
    explicit_feedback_score: float
    product_quality_score: float
    merchant_quality_score: float
    provenance: tuple[FeatureProvenance, ...] = ()


@dataclass(frozen=True)
class EligibilityResult:
    """Outcome of the mandatory hard eligibility & safety gate."""

    eligible: bool
    size_availability: SizeAvailability
    reason_codes: tuple[str, ...] = ()


class RankedProductItem(BaseModel):
    """Shopper-facing ranked product item without exposing private profile data."""

    product_id: str
    merchant_offer_id: str
    title: str
    category_id: str
    price: Decimal | None = None
    currency: str | None = None
    position: int
    ranking_score: float
    availability: AvailabilityStatus
    size_availability: SizeAvailability
    selected_size_available: bool
    reasons: list[RankingReasonCode]
    reason_labels: list[str]
    is_sponsored: bool = False
    availability_verified_at: datetime | None = None
    ranking_version: str


class RankingPagination(BaseModel):
    page: int
    page_size: int
    total_eligible: int
    has_more: bool


class RankedProductsResponse(BaseModel):
    """Versioned personalized or baseline ranking API response."""

    request_id: str
    ranking_version: str
    config_version: str
    taxonomy_version: str
    cache_hit: bool = False
    results: list[RankedProductItem]
    pagination: RankingPagination
