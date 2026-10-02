"""FashXStudio Product & Fashion Detail Screens System Contracts — Phase 09.

Defines Pydantic v2 data contracts for Product & Fashion Detail (Sections 9.1-9.83):
- Screen Inventory: P01-P10 Product Detail Screens, F01-F09 Fashion Detail Screens
- Product Detail Architecture: Gallery with zoom, price, availability, variant selection with cross-dependencies,
  quantity controls, progressive specifications, reviews with distribution, similar/recommended/styled-with relationships.
- Fashion Detail Architecture: Story, Article, Collection, Look with hotspots, Inspiration, Brand Story, Editorial canvas.
- Relationship Engine: Distinguishes Similar vs Recommended vs Styled With vs Curated.
- State Resilience: Partial failure isolation, progressive skeletons, and authoritative error recovery.

All schemas enforce extra="forbid" via BaseContractModel (Constitution Rule I02).
"""

from enum import StrEnum
from typing import Any
from pydantic import Field
from schemas.base import BaseContractModel
from schemas.visual.fashion import VisualContentModel


# ---------------------------------------------------------------------------
# Enums (Sections 9.2, 9.6, 9.11, 9.13, 9.26, 9.47)
# ---------------------------------------------------------------------------

class DetailScreenId(StrEnum):
    """Screen identifiers for Product & Fashion Detail ecosystem (Section 9.2)."""
    # Product Screens (P01 - P10)
    P01_PRODUCT_LISTING = "P01"
    P02_PRODUCT_DETAIL = "P02"
    P03_PRODUCT_GALLERY = "P03"
    P04_PRODUCT_VARIANT_SELECTION = "P04"
    P05_PRODUCT_REVIEWS = "P05"
    P06_PRODUCT_SPECIFICATIONS = "P06"
    P07_SIMILAR_PRODUCTS = "P07"
    P08_RECOMMENDED_PRODUCTS = "P08"
    P09_PRODUCT_COMPARISON = "P09"
    P10_PRODUCT_AVAILABILITY = "P10"

    # Fashion Screens (F01 - F09)
    F01_FASHION_HOME = "F01"
    F02_FASHION_FEED = "F02"
    F03_FASHION_STORY = "F03"
    F04_FASHION_ARTICLE = "F04"
    F05_FASHION_COLLECTION = "F05"
    F06_FASHION_LOOK = "F06"
    F07_FASHION_INSPIRATION = "F07"
    F08_BRAND_STORY = "F08"
    F09_EDITORIAL_VIEW = "F09"


class ProductAvailabilityState(StrEnum):
    """Authoritative inventory availability states (Section 9.11)."""
    IN_STOCK = "in_stock"
    LOW_STOCK = "low_stock"
    OUT_OF_STOCK = "out_of_stock"
    PRE_ORDER = "pre_order"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"


class MediaType(StrEnum):
    """Media asset categorization (Section 9.6)."""
    IMAGE = "image"
    THUMBNAIL = "thumbnail"
    DETAIL = "detail"
    LIFESTYLE = "lifestyle"
    MODEL = "model"
    VIDEO = "video"
    VIEW_360 = "view_360"


class VariantOptionState(StrEnum):
    """Variant option availability and selection state (Section 9.13)."""
    AVAILABLE = "available"
    SELECTED = "selected"
    UNAVAILABLE = "unavailable"
    LOADING = "loading"


class RelatedItemRelationship(StrEnum):
    """Explicit semantic distinction between content connections (Section 9.26)."""
    SIMILAR = "similar"
    RECOMMENDED = "recommended"
    STYLED_WITH = "styled_with"
    RECENTLY_VIEWED = "recently_viewed"
    TRENDING = "trending"


class DetailState(StrEnum):
    """Unified screen and module lifecycle state (Sections 9.47, 9.48, 9.67)."""
    LOADING = "loading"
    READY = "ready"
    PARTIAL = "partial"
    EMPTY = "empty"
    ERROR = "error"
    NOT_FOUND = "not_found"
    UNAVAILABLE = "unavailable"


# ---------------------------------------------------------------------------
# Navigation & Gallery Models (Sections 9.4, 9.6, 9.7, 9.8, 9.51)
# ---------------------------------------------------------------------------

class BreadcrumbItemContract(BaseContractModel):
    """Canonical hierarchy breadcrumb item (Section 9.51)."""
    label: str
    route: str
    is_current: bool = Field(default=False)


class MediaItemContract(BaseContractModel):
    """Individual media asset specification (Section 9.6)."""
    id: str
    uri: str
    media_type: MediaType = Field(default=MediaType.IMAGE)
    alt_text: str
    aspect_ratio: str = Field(default="3:4")
    is_primary: bool = Field(default=False)
    order: int = Field(default=0)


class ProductGalleryContract(BaseContractModel):
    """Interactive media gallery supporting thumbnail navigation and zoom (Sections 9.7, 9.8)."""
    items: list[MediaItemContract] = Field(default_factory=list)
    active_index: int = Field(default=0, ge=0)
    zoom_enabled: bool = Field(default=True)


# ---------------------------------------------------------------------------
# Variant & Specification Models (Sections 9.12 - 9.15, 9.19, 9.20)
# ---------------------------------------------------------------------------

class VariantOptionItemContract(BaseContractModel):
    """Single selectable variant choice (Section 9.12)."""
    id: str
    label: str
    value: str
    state: VariantOptionState = Field(default=VariantOptionState.AVAILABLE)
    swatch_hex: str | None = Field(default=None)


class VariantGroupContract(BaseContractModel):
    """Group of related variant dimensions (e.g. Size, Color) (Section 9.12 & 9.14)."""
    group_id: str
    name: str
    options: list[VariantOptionItemContract] = Field(default_factory=list)
    selected_option_id: str | None = Field(default=None)


class SpecificationItemContract(BaseContractModel):
    """Individual key-value specification row (Section 9.19)."""
    label: str
    value: str


class SpecificationSectionContract(BaseContractModel):
    """Grouped technical specification category (Section 9.20)."""
    group_name: str
    items: list[SpecificationItemContract] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Reviews & Social Proof Models (Sections 9.21 - 9.23)
# ---------------------------------------------------------------------------

class ReviewDistributionItemContract(BaseContractModel):
    """Histogram bar for star rating distribution (Section 9.21)."""
    stars: int = Field(ge=1, le=5)
    count: int = Field(default=0, ge=0)
    percentage: float = Field(default=0.0, ge=0.0, le=100.0)


class ProductReviewItemContract(BaseContractModel):
    """Verified user product review card (Section 9.22)."""
    id: str
    author: str
    rating: int = Field(ge=1, le=5)
    date: str
    comment: str
    is_verified: bool = Field(default=False)
    helpful_count: int = Field(default=0, ge=0)


class ProductReviewsContract(BaseContractModel):
    """Comprehensive product review summary and list (Section 9.21, 9.23)."""
    average_rating: float = Field(default=0.0, ge=0.0, le=5.0)
    total_reviews: int = Field(default=0, ge=0)
    distribution: list[ReviewDistributionItemContract] = Field(default_factory=list)
    reviews: list[ProductReviewItemContract] = Field(default_factory=list)
    state: DetailState = Field(default=DetailState.READY)


# ---------------------------------------------------------------------------
# Content Relationships & Comparison (Sections 9.24 - 9.27, 9.31, 9.32)
# ---------------------------------------------------------------------------

class RelatedProductItemContract(BaseContractModel):
    """Semantically tagged connected product item (Sections 9.24 - 9.27)."""
    relationship: RelatedItemRelationship
    product_id: str
    title: str
    brand: str
    image_uri: str
    price: float = Field(ge=0.0)
    original_price: float | None = Field(default=None, ge=0.0)
    reason: str | None = Field(default=None)


class LookHotspotContract(BaseContractModel):
    """Interactive hotspot mapping garment onto styled look media (Section 9.38)."""
    product_id: str
    label: str
    x_percent: float = Field(ge=0.0, le=100.0)
    y_percent: float = Field(ge=0.0, le=100.0)


class LookItemLinkContract(BaseContractModel):
    """Direct product link constituent within styled look (Section 9.37, 9.38)."""
    slot: str
    product_id: str
    title: str
    brand: str
    price: float = Field(ge=0.0)
    image_uri: str


class AttributeComparisonItemContract(BaseContractModel):
    """Single attribute comparison row across multiple products (Section 9.31)."""
    attribute_name: str
    values: dict[str, str] = Field(default_factory=dict)


class ProductComparisonDetailContract(BaseContractModel):
    """Structured side-by-side comparison specification (Section 9.31, 9.32)."""
    product_ids: list[str] = Field(default_factory=list)
    products: list[dict[str, Any]] = Field(default_factory=list)
    attributes: list[AttributeComparisonItemContract] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Product View Models & Templates (P02, P05, P09, P10, Section 9.60 - 9.62)
# ---------------------------------------------------------------------------

class ProductDetailViewModelContract(BaseContractModel):
    """Comprehensive, decoupled view model for Product Detail Screen (Section 9.62)."""
    id: str
    brand: str
    title: str
    price: float = Field(ge=0.0)
    original_price: float | None = Field(default=None, ge=0.0)
    currency: str = Field(default="INR")
    discount_percentage: int | None = Field(default=None, ge=0, le=100)
    rating: float = Field(default=0.0, ge=0.0, le=5.0)
    review_count: int = Field(default=0, ge=0)
    availability: ProductAvailabilityState = Field(default=ProductAvailabilityState.IN_STOCK)
    stock_units: int | None = Field(default=None, ge=0)
    short_summary: str
    description: str
    gallery: ProductGalleryContract
    variant_groups: list[VariantGroupContract] = Field(default_factory=list)
    specifications: list[SpecificationSectionContract] = Field(default_factory=list)
    reviews: ProductReviewsContract
    similar_products: list[RelatedProductItemContract] = Field(default_factory=list)
    recommended_products: list[RelatedProductItemContract] = Field(default_factory=list)
    styled_with: list[RelatedProductItemContract] = Field(default_factory=list)
    breadcrumbs: list[BreadcrumbItemContract] = Field(default_factory=list)
    state: DetailState = Field(default=DetailState.READY)


class ComprehensiveProductDetailTemplateSpecContract(BaseContractModel):
    """P02: Product Detail screen template specification (Sections 9.4, 9.5, 9.60)."""
    screen_id: DetailScreenId = Field(default=DetailScreenId.P02_PRODUCT_DETAIL)
    view_model: ProductDetailViewModelContract


class ProductReviewsTemplateSpecContract(BaseContractModel):
    """P05: Dedicated Product Reviews screen template specification (Section 9.21, 9.60)."""
    screen_id: DetailScreenId = Field(default=DetailScreenId.P05_PRODUCT_REVIEWS)
    product_id: str
    reviews: ProductReviewsContract


class ProductAvailabilityTemplateSpecContract(BaseContractModel):
    """P10: Detailed Product Availability & Delivery screen template (Section 9.11, 9.60)."""
    screen_id: DetailScreenId = Field(default=DetailScreenId.P10_PRODUCT_AVAILABILITY)
    product_id: str
    availability: ProductAvailabilityState
    stock_units: int | None = Field(default=None, ge=0)
    estimated_delivery_days: int = Field(default=3, ge=1)
    postal_code_supported: bool = Field(default=True)
    shipping_origin: str = Field(default="Central Distribution Hub")


class ProductComparisonTemplateSpecContract(BaseContractModel):
    """P09: Dedicated Product Comparison screen template specification (Section 9.31, 9.60)."""
    screen_id: DetailScreenId = Field(default=DetailScreenId.P09_PRODUCT_COMPARISON)
    comparison: ProductComparisonDetailContract


# ---------------------------------------------------------------------------
# Fashion View Models & Templates (F03 - F09, Section 9.33 - 9.44, 9.60, 9.63)
# ---------------------------------------------------------------------------

class FashionStoryDetailTemplateSpecContract(BaseContractModel):
    """F03: Fashion Story template specification (Section 9.34)."""
    screen_id: DetailScreenId = Field(default=DetailScreenId.F03_FASHION_STORY)
    id: str
    title: str
    subtitle: str
    author: str
    published_date: str
    category: str
    hero_media_uri: str
    content_markdown: str
    related_looks: list[VisualContentModel] = Field(default_factory=list)
    related_products: list[VisualContentModel] = Field(default_factory=list)
    state: DetailState = Field(default=DetailState.READY)


class FashionArticleDetailTemplateSpecContract(BaseContractModel):
    """F04: Fashion Article template specification (Section 9.35)."""
    screen_id: DetailScreenId = Field(default=DetailScreenId.F04_FASHION_ARTICLE)
    id: str
    category: str
    title: str
    subtitle: str
    author: str
    published_date: str
    hero_media_uri: str
    body_markdown: str
    inline_media_uris: list[str] = Field(default_factory=list)
    related_products: list[VisualContentModel] = Field(default_factory=list)
    state: DetailState = Field(default=DetailState.READY)


class FashionCollectionDetailTemplateSpecContract(BaseContractModel):
    """F05: Fashion Collection template specification (Section 9.40)."""
    screen_id: DetailScreenId = Field(default=DetailScreenId.F05_FASHION_COLLECTION)
    id: str
    name: str
    season: str
    description: str
    curator: str
    hero_image_uri: str
    looks: list[VisualContentModel] = Field(default_factory=list)
    products: list[VisualContentModel] = Field(default_factory=list)
    styles: list[VisualContentModel] = Field(default_factory=list)
    related_collections: list[VisualContentModel] = Field(default_factory=list)
    state: DetailState = Field(default=DetailState.READY)


class FashionLookDetailTemplateSpecContract(BaseContractModel):
    """F06: Fashion Look template specification (Section 9.37, 9.39)."""
    screen_id: DetailScreenId = Field(default=DetailScreenId.F06_FASHION_LOOK)
    id: str
    name: str
    style: str
    context_description: str
    hero_image_uri: str
    outfit_items: list[LookItemLinkContract] = Field(default_factory=list)
    hotspots: list[LookHotspotContract] = Field(default_factory=list)
    related_looks: list[VisualContentModel] = Field(default_factory=list)
    is_saved: bool = Field(default=False)
    state: DetailState = Field(default=DetailState.READY)


class FashionInspirationDetailTemplateSpecContract(BaseContractModel):
    """F07: Fashion Inspiration template specification (Section 9.43)."""
    screen_id: DetailScreenId = Field(default=DetailScreenId.F07_FASHION_INSPIRATION)
    id: str
    title: str
    context: str
    media_uri: str
    style_tags: list[str] = Field(default_factory=list)
    related_looks: list[VisualContentModel] = Field(default_factory=list)
    related_products: list[VisualContentModel] = Field(default_factory=list)
    is_saved: bool = Field(default=False)
    state: DetailState = Field(default=DetailState.READY)


class BrandStoryDetailTemplateSpecContract(BaseContractModel):
    """F08: Brand Story template specification (Section 9.42)."""
    screen_id: DetailScreenId = Field(default=DetailScreenId.F08_BRAND_STORY)
    id: str
    brand_name: str
    hero_image_uri: str
    logo_uri: str
    story_markdown: str
    values: list[str] = Field(default_factory=list)
    collections: list[VisualContentModel] = Field(default_factory=list)
    featured_products: list[VisualContentModel] = Field(default_factory=list)
    featured_looks: list[VisualContentModel] = Field(default_factory=list)
    is_verified: bool = Field(default=True)
    state: DetailState = Field(default=DetailState.READY)


class EditorialViewTemplateSpecContract(BaseContractModel):
    """F09: Curated Editorial View template specification (Section 9.36)."""
    screen_id: DetailScreenId = Field(default=DetailScreenId.F09_EDITORIAL_VIEW)
    id: str
    title: str
    hero_media_uri: str
    narrative_blocks: list[dict[str, str]] = Field(default_factory=list)
    curated_looks: list[VisualContentModel] = Field(default_factory=list)
    curated_products: list[VisualContentModel] = Field(default_factory=list)
    state: DetailState = Field(default=DetailState.READY)
