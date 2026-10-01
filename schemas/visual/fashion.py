"""FashXStudio Fashion Content System Contracts — Phase 06.

Defines Pydantic v2 data contracts for the Fashion Content Design System (Sections 6.1-6.62):
- Content Objects: Product, Look, Outfit, Collection, Style, Trend, Brand, Story, Article, Editorial, Recommendation
- Visual Grammar & Content Model: VisualContentModel, ContentType, ContentState, ModerationState
- Save & Share Interactions: SaveState, SaveToggleResultContract
- Fashion Templates: ListingTemplate, DetailTemplate, EditorialTemplate, CollectionTemplate, DiscoveryTemplate

All schemas enforce extra="forbid" via BaseContractModel (Constitution Rule I02).
"""

from enum import StrEnum
from typing import Any
from pydantic import Field
from schemas.base import BaseContractModel
from schemas.visual.components import PriceSpecContract, RatingSpecContract


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class FashionContentType(StrEnum):
    """Fashion content object taxonomy (Section 6.2 & 6.3)."""
    PRODUCT = "product"
    LOOK = "look"
    OUTFIT = "outfit"
    COLLECTION = "collection"
    STYLE = "style"
    TREND = "trend"
    BRAND = "brand"
    STORY = "story"
    ARTICLE = "article"
    EDITORIAL = "editorial"
    RECOMMENDATION = "recommendation"


class ContentState(StrEnum):
    """Content availability states (Section 6.46)."""
    LOADING = "loading"
    LOADED = "loaded"
    EMPTY = "empty"
    UNAVAILABLE = "unavailable"
    ERROR = "error"
    PARTIAL = "partial"


class ModerationState(StrEnum):
    """Content safety and moderation boundary states (Section 6.48)."""
    VISIBLE = "visible"
    RESTRICTED = "restricted"
    UNAVAILABLE = "unavailable"
    REMOVED = "removed"
    PENDING = "pending"


class TrendMomentum(StrEnum):
    """Trend trajectory signals (Section 6.17)."""
    EMERGING = "emerging"
    PEAKING = "peaking"
    STABLE = "stable"
    DECLINING = "declining"


class SaveState(StrEnum):
    """Save interaction lifecycle (Section 6.28 & 6.29)."""
    UNSAVED = "unsaved"
    SAVING = "saving"
    SAVED = "saved"
    ERROR = "error"


class ContentSourceType(StrEnum):
    """Content transparency origin (Section 6.53)."""
    OFFICIAL_MERCHANT = "official_merchant"
    EDITORIAL = "editorial"
    COMMUNITY = "community"
    SYSTEM_RECOMMENDATION = "system_recommendation"
    AI_GENERATED = "ai_generated"


# ---------------------------------------------------------------------------
# Core Content Objects (Sections 6.6 - 6.24)
# ---------------------------------------------------------------------------

class ProductItemContract(BaseContractModel):
    """Fashion Product content representation (Section 6.6 & 6.7)."""
    id: str
    brand: str
    title: str
    primary_image_uri: str
    alternate_image_uris: list[str] = Field(default_factory=list)
    price: PriceSpecContract
    rating: RatingSpecContract | None = Field(default=None)
    category: str
    is_saved: bool = Field(default=False)
    is_in_stock: bool = Field(default=True)
    badge: str | None = Field(default=None)
    attributes: dict[str, str] = Field(default_factory=dict)
    state: ContentState = Field(default=ContentState.LOADED)
    moderation_state: ModerationState = Field(default=ModerationState.VISIBLE)


class LookItemContract(BaseContractModel):
    """Fashion Look visual composition (Section 6.10)."""
    id: str
    title: str
    style_name: str
    hero_image_uri: str
    items_count: int = Field(default=1, ge=1)
    associated_product_ids: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    is_saved: bool = Field(default=False)
    curator_name: str | None = Field(default=None)
    state: ContentState = Field(default=ContentState.LOADED)


class OutfitPieceMappingContract(BaseContractModel):
    """Outfit piece slot mapping (Section 6.11 & 6.12)."""
    slot: str = Field(..., description="top | bottom | shoes | accessory | outerwear")
    product_id: str
    product_title: str
    image_uri: str
    price: PriceSpecContract


class OutfitItemContract(BaseContractModel):
    """Outfit item combination with constituent mapped pieces (Section 6.11)."""
    id: str
    title: str
    image_uri: str
    pieces: list[OutfitPieceMappingContract] = Field(default_factory=list)
    is_saved: bool = Field(default=False)
    total_price: PriceSpecContract | None = Field(default=None)
    state: ContentState = Field(default=ContentState.LOADED)


class CollectionItemContract(BaseContractModel):
    """Curated fashion collection representation (Section 6.13 & 6.14)."""
    id: str
    title: str
    description: str
    hero_image_uri: str
    item_count: int = Field(default=0, ge=0)
    season_tag: str | None = Field(default=None)
    featured_product_ids: list[str] = Field(default_factory=list)
    is_saved: bool = Field(default=False)
    state: ContentState = Field(default=ContentState.LOADED)


class StyleCategoryContract(BaseContractModel):
    """Data-driven style aesthetic category (Section 6.15 & 6.16)."""
    id: str
    name: str
    description: str
    image_uri: str
    look_count: int = Field(default=0, ge=0)
    associated_tags: list[str] = Field(default_factory=list)


class TrendSignalPointContract(BaseContractModel):
    """Trend timeline data point (Section 6.19)."""
    timestamp: str
    signal_label: str
    intensity: float = Field(ge=0.0, le=1.0)


class TrendItemContract(BaseContractModel):
    """Emerging and popular trend representation (Section 6.17 - 6.19)."""
    id: str
    title: str
    category: str
    image_uri: str
    momentum: TrendMomentum = Field(default=TrendMomentum.EMERGING)
    regions: list[str] = Field(default_factory=list)
    timeline: list[TrendSignalPointContract] = Field(default_factory=list)
    associated_product_ids: list[str] = Field(default_factory=list)
    state: ContentState = Field(default=ContentState.LOADED)


class BrandItemContract(BaseContractModel):
    """Fashion brand identity representation (Section 6.20 & 6.21)."""
    id: str
    name: str
    logo_uri: str
    cover_image_uri: str | None = Field(default=None)
    category: str
    description: str | None = Field(default=None)
    product_count: int = Field(default=0, ge=0)
    is_verified: bool = Field(default=True)


class FashionStoryContract(BaseContractModel):
    """Editorial narrative fashion story (Section 6.22 - 6.24)."""
    id: str
    title: str
    subtitle: str | None = Field(default=None)
    hero_image_uri: str
    author: str
    published_date: str
    content_markdown: str
    category: str
    related_product_ids: list[str] = Field(default_factory=list)
    related_look_ids: list[str] = Field(default_factory=list)
    state: ContentState = Field(default=ContentState.LOADED)


class RecommendationItemContract(BaseContractModel):
    """AI Recommendation representation with explainability (Section 6.31 & 6.32)."""
    id: str
    target_content_type: FashionContentType
    product: ProductItemContract
    recommendation_label: str = Field(default="Recommended for you")
    explanation_reason: str = Field(..., description="Why this appears (Section 6.31)")
    confidence_score: float = Field(ge=0.0, le=1.0)
    source_type: ContentSourceType = Field(default=ContentSourceType.SYSTEM_RECOMMENDATION)


# ---------------------------------------------------------------------------
# Visual Content Model & Feed (Sections 6.25 & 6.52)
# ---------------------------------------------------------------------------

class VisualContentModel(BaseContractModel):
    """Unified polymorphic visual content adapter model (Section 6.52)."""
    id: str
    content_type: FashionContentType
    title: str
    subtitle: str | None = Field(default=None)
    media_uri: str
    category_label: str
    price: PriceSpecContract | None = Field(default=None)
    rating: RatingSpecContract | None = Field(default=None)
    labels: list[str] = Field(default_factory=list)
    is_saved: bool = Field(default=False)
    state: ContentState = Field(default=ContentState.LOADED)
    source: ContentSourceType = Field(default=ContentSourceType.OFFICIAL_MERCHANT)
    relationships: dict[str, list[str]] = Field(default_factory=dict)


class FashionFeedContract(BaseContractModel):
    """Mixed-content discovery feed payload (Section 6.25 & 6.47)."""
    feed_id: str
    title: str
    items: list[VisualContentModel] = Field(default_factory=list)
    has_partial_content: bool = Field(default=False)
    total_items: int = Field(default=0)


class SaveToggleRequestContract(BaseContractModel):
    """Request contract for toggling save state on a fashion content item."""
    content_id: str
    content_type: FashionContentType
    current_saved: bool


class SaveToggleResultContract(BaseContractModel):
    """Response contract for saving/unsaving fashion content (Section 6.28 & 6.29)."""
    content_id: str
    content_type: FashionContentType
    is_saved: bool
    state: SaveState
    message: str


# ---------------------------------------------------------------------------
# Fashion Content Templates (Section 6.35 - 6.40, 6.50)
# ---------------------------------------------------------------------------

class ListingTemplateSpecContract(BaseContractModel):
    """Listing screen template specification (Section 6.36)."""
    title: str
    active_filters_count: int = Field(default=0)
    sort_options: list[str] = Field(default_factory=list)
    selected_sort: str = Field(default="Relevance")
    items: list[VisualContentModel] = Field(default_factory=list)
    total_count: int = Field(default=0)
    current_page: int = Field(default=1)
    total_pages: int = Field(default=1)


class DetailTemplateSpecContract(BaseContractModel):
    """Detail screen template specification (Section 6.37)."""
    content_id: str
    content_type: FashionContentType
    breadcrumb_trail: list[str] = Field(default_factory=list)
    primary_item: VisualContentModel
    related_items: list[VisualContentModel] = Field(default_factory=list)
    recommendations: list[RecommendationItemContract] = Field(default_factory=list)


class EditorialTemplateSpecContract(BaseContractModel):
    """Editorial narrative template specification (Section 6.38)."""
    story: FashionStoryContract
    inline_products: list[ProductItemContract] = Field(default_factory=list)
    related_looks: list[LookItemContract] = Field(default_factory=list)
    more_stories: list[FashionStoryContract] = Field(default_factory=list)


class CollectionTemplateSpecContract(BaseContractModel):
    """Collection showcase template specification (Section 6.39)."""
    collection: CollectionItemContract
    featured_products: list[ProductItemContract] = Field(default_factory=list)
    curated_looks: list[LookItemContract] = Field(default_factory=list)


class DiscoveryTemplateSpecContract(BaseContractModel):
    """Mixed discovery surface template specification (Section 6.40)."""
    featured_story: FashionStoryContract | None = Field(default=None)
    trending_items: list[TrendItemContract] = Field(default_factory=list)
    curated_collections: list[CollectionItemContract] = Field(default_factory=list)
    recommended_products: list[RecommendationItemContract] = Field(default_factory=list)
    featured_brands: list[BrandItemContract] = Field(default_factory=list)
