"""Fashion Content Service — Phase 06.

Provides the fashion content domain adapter, visual content modeling, feed generation,
content state transitions, save/share mechanics, and content templates (Sections 6.1-6.62).
Adheres to Rule I01 (Layer Separation) and Rule I02 (Contract Primacy).
"""

from typing import Any
from schemas.visual.components import PriceSpecContract, RatingSpecContract
from schemas.visual.fashion import (
    BrandItemContract,
    CollectionItemContract,
    CollectionTemplateSpecContract,
    ContentSourceType,
    ContentState,
    DetailTemplateSpecContract,
    DiscoveryTemplateSpecContract,
    EditorialTemplateSpecContract,
    FashionContentType,
    FashionFeedContract,
    FashionStoryContract,
    ListingTemplateSpecContract,
    LookItemContract,
    ModerationState,
    OutfitItemContract,
    OutfitPieceMappingContract,
    ProductItemContract,
    RecommendationItemContract,
    SaveState,
    SaveToggleResultContract,
    StyleCategoryContract,
    TrendItemContract,
    TrendMomentum,
    TrendSignalPointContract,
    VisualContentModel,
)


# ---------------------------------------------------------------------------
# Canonical Fashion Content Fixtures
# ---------------------------------------------------------------------------

SAMPLE_PRODUCTS: list[ProductItemContract] = [
    ProductItemContract(
        id="prod-denim-01",
        brand="RawDenim Co.",
        title="Selvedge Oversized Denim Jacket",
        primary_image_uri="https://images.fashx.com/products/denim_jacket_front.jpg",
        alternate_image_uris=[
            "https://images.fashx.com/products/denim_jacket_back.jpg",
            "https://images.fashx.com/products/denim_jacket_detail.jpg",
        ],
        price=PriceSpecContract(amount=4999.0, original_amount=6999.0, discount_percentage=28),
        rating=RatingSpecContract(value=4.7, rating_count=142),
        category="Outerwear",
        is_saved=False,
        is_in_stock=True,
        badge="BESTSELLER",
        attributes={"fabric": "14oz Japanese Selvedge", "fit": "Relaxed Boxy", "origin": "Kojima"},
    ),
    ProductItemContract(
        id="prod-linen-02",
        brand="Breeze & Loom",
        title="Relaxed Camp Collar Linen Shirt",
        primary_image_uri="https://images.fashx.com/products/linen_shirt_sand.jpg",
        alternate_image_uris=["https://images.fashx.com/products/linen_shirt_model.jpg"],
        price=PriceSpecContract(amount=2499.0),
        rating=RatingSpecContract(value=4.5, rating_count=88),
        category="Tops",
        is_saved=True,
        is_in_stock=True,
        badge="ORGANIC",
        attributes={"fabric": "100% French Flax", "collar": "Cuban Camp"},
    ),
]

SAMPLE_LOOKS: list[LookItemContract] = [
    LookItemContract(
        id="look-mumbai-01",
        title="Bandra Sunday Street Style",
        style_name="Urban Relaxed",
        hero_image_uri="https://images.fashx.com/looks/bandra_street.jpg",
        items_count=4,
        associated_product_ids=["prod-denim-01", "prod-linen-02"],
        tags=["Streetwear", "Coastal", "Layered"],
        is_saved=True,
        curator_name="Aarav Mehta",
    ),
]

SAMPLE_OUTFITS: list[OutfitItemContract] = [
    OutfitItemContract(
        id="outfit-monsoon-01",
        title="High-Humidity Layered Ensemble",
        image_uri="https://images.fashx.com/outfits/monsoon_ensemble.jpg",
        pieces=[
            OutfitPieceMappingContract(
                slot="outerwear",
                product_id="prod-denim-01",
                product_title="Selvedge Oversized Denim Jacket",
                image_uri="https://images.fashx.com/products/denim_jacket_front.jpg",
                price=PriceSpecContract(amount=4999.0),
            ),
            OutfitPieceMappingContract(
                slot="top",
                product_id="prod-linen-02",
                product_title="Relaxed Camp Collar Linen Shirt",
                image_uri="https://images.fashx.com/products/linen_shirt_sand.jpg",
                price=PriceSpecContract(amount=2499.0),
            ),
        ],
        is_saved=False,
        total_price=PriceSpecContract(amount=7498.0),
    ),
]

SAMPLE_COLLECTIONS: list[CollectionItemContract] = [
    CollectionItemContract(
        id="coll-monsoon-26",
        title="Monsoon Transitional '26",
        description="Hydrophobic natural fibers, breathable weaves, and muted mineral palettes for coastal monsoons.",
        hero_image_uri="https://images.fashx.com/collections/monsoon_hero.jpg",
        item_count=36,
        season_tag="Monsoon 2026",
        featured_product_ids=["prod-denim-01", "prod-linen-02"],
        is_saved=True,
    ),
]

SAMPLE_STYLES: list[StyleCategoryContract] = [
    StyleCategoryContract(
        id="style-streetwear",
        name="Contemporary Streetwear",
        description="Boxy proportions, utilitarian details, and raw textiles.",
        image_uri="https://images.fashx.com/styles/streetwear.jpg",
        look_count=128,
        associated_tags=["Oversized", "Denim", "Sneakers"],
    ),
]

SAMPLE_TRENDS: list[TrendItemContract] = [
    TrendItemContract(
        id="trend-raw-textures",
        title="Unfinished Raw Textures",
        category="Textiles",
        image_uri="https://images.fashx.com/trends/raw_textures.jpg",
        momentum=TrendMomentum.EMERGING,
        regions=["Mumbai", "Delhi", "Bengaluru"],
        timeline=[
            TrendSignalPointContract(timestamp="2026-06", signal_label="Runway emergence", intensity=0.3),
            TrendSignalPointContract(timestamp="2026-08", signal_label="Street adoption", intensity=0.65),
            TrendSignalPointContract(timestamp="2026-10", signal_label="Retail proliferation", intensity=0.88),
        ],
        associated_product_ids=["prod-denim-01"],
    ),
]

SAMPLE_BRANDS: list[BrandItemContract] = [
    BrandItemContract(
        id="brand-raw-denim",
        name="RawDenim Co.",
        logo_uri="https://images.fashx.com/brands/rawdenim_logo.png",
        cover_image_uri="https://images.fashx.com/brands/rawdenim_cover.jpg",
        category="Artisanal Denim",
        description="Specializing in shuttle-loom selvedge denim crafted with indigo vegetable dyes.",
        product_count=48,
        is_verified=True,
    ),
]

SAMPLE_STORIES: list[FashionStoryContract] = [
    FashionStoryContract(
        id="story-coastal-layering",
        title="The Art of Coastal Humidity Layering",
        subtitle="How coastal street youth balance boxy tailoring with monsoon downpours.",
        hero_image_uri="https://images.fashx.com/stories/coastal_layering.jpg",
        author="Kavya Sharma, Fashion Editor",
        published_date="2026-09-28",
        content_markdown="Coastal weather demands that layering be architectural rather than thermal...",
        category="Editorial",
        related_product_ids=["prod-denim-01", "prod-linen-02"],
        related_look_ids=["look-mumbai-01"],
    ),
]

SAMPLE_RECOMMENDATIONS: list[RecommendationItemContract] = [
    RecommendationItemContract(
        id="rec-denim-jacket",
        target_content_type=FashionContentType.PRODUCT,
        product=SAMPLE_PRODUCTS[0],
        recommendation_label="Curated for Your Style Profile",
        explanation_reason="Aligns with your explored interest in Japanese selvedge denim and boxy silhouettes.",
        confidence_score=0.94,
        source_type=ContentSourceType.AI_GENERATED,
    ),
]


# ---------------------------------------------------------------------------
# Visual Content Model Adapter (Section 6.51 & 6.52)
# ---------------------------------------------------------------------------

def to_visual_content_model(item: Any, content_type: FashionContentType) -> VisualContentModel:
    """Transform any domain content object into the unified VisualContentModel."""
    if content_type == FashionContentType.PRODUCT:
        p: ProductItemContract = item
        return VisualContentModel(
            id=p.id,
            content_type=content_type,
            title=p.title,
            subtitle=p.brand,
            media_uri=p.primary_image_uri,
            category_label=p.category,
            price=p.price,
            rating=p.rating,
            labels=[p.badge] if p.badge else [],
            is_saved=p.is_saved,
            state=p.state,
            source=ContentSourceType.OFFICIAL_MERCHANT,
            relationships={},
        )
    elif content_type == FashionContentType.LOOK:
        l: LookItemContract = item
        return VisualContentModel(
            id=l.id,
            content_type=content_type,
            title=l.title,
            subtitle=f"{l.items_count} items by {l.curator_name or 'Community'}",
            media_uri=l.hero_image_uri,
            category_label=l.style_name,
            labels=l.tags,
            is_saved=l.is_saved,
            state=l.state,
            source=ContentSourceType.EDITORIAL,
            relationships={"products": l.associated_product_ids},
        )
    elif content_type == FashionContentType.COLLECTION:
        c: CollectionItemContract = item
        return VisualContentModel(
            id=c.id,
            content_type=content_type,
            title=c.title,
            subtitle=c.season_tag,
            media_uri=c.hero_image_uri,
            category_label="Collection",
            labels=[f"{c.item_count} items"],
            is_saved=c.is_saved,
            state=c.state,
            source=ContentSourceType.EDITORIAL,
            relationships={"products": c.featured_product_ids},
        )
    elif content_type == FashionContentType.TREND:
        t: TrendItemContract = item
        return VisualContentModel(
            id=t.id,
            content_type=content_type,
            title=t.title,
            subtitle=f"Momentum: {str(t.momentum).upper()}",
            media_uri=t.image_uri,
            category_label=t.category,
            labels=t.regions,
            is_saved=False,
            state=t.state,
            source=ContentSourceType.SYSTEM_RECOMMENDATION,
            relationships={"products": t.associated_product_ids},
        )
    elif content_type == FashionContentType.STORY:
        s: FashionStoryContract = item
        return VisualContentModel(
            id=s.id,
            content_type=content_type,
            title=s.title,
            subtitle=s.author,
            media_uri=s.hero_image_uri,
            category_label=s.category,
            labels=["Editorial"],
            is_saved=False,
            state=s.state,
            source=ContentSourceType.EDITORIAL,
            relationships={"products": s.related_product_ids, "looks": s.related_look_ids},
        )
    else:
        return VisualContentModel(
            id=getattr(item, "id", "unknown"),
            content_type=content_type,
            title=getattr(item, "title", getattr(item, "name", "Fashion Item")),
            media_uri=getattr(item, "image_uri", getattr(item, "logo_uri", "")),
            category_label=getattr(item, "category", "Fashion"),
            labels=[],
            is_saved=getattr(item, "is_saved", False),
            state=getattr(item, "state", ContentState.LOADED),
        )


# ---------------------------------------------------------------------------
# Feed & Discovery Engine (Section 6.25 & 6.47)
# ---------------------------------------------------------------------------

def get_fashion_feed(
    page: int = 1,
    limit: int = 10,
    content_type: FashionContentType | None = None,
) -> FashionFeedContract:
    """Generate a polymorphic fashion discovery feed combining mixed content."""
    items: list[VisualContentModel] = []

    for s in SAMPLE_STORIES:
        items.append(to_visual_content_model(s, FashionContentType.STORY))
    for l in SAMPLE_LOOKS:
        items.append(to_visual_content_model(l, FashionContentType.LOOK))
    for p in SAMPLE_PRODUCTS:
        items.append(to_visual_content_model(p, FashionContentType.PRODUCT))
    for t in SAMPLE_TRENDS:
        items.append(to_visual_content_model(t, FashionContentType.TREND))
    for c in SAMPLE_COLLECTIONS:
        items.append(to_visual_content_model(c, FashionContentType.COLLECTION))

    if content_type is not None:
        items = [i for i in items if i.content_type == content_type]

    total = len(items)
    start = (page - 1) * limit
    paginated = items[start: start + limit]

    return FashionFeedContract(
        feed_id=f"feed-mixed-p{page}",
        title="FashXStudio Curated Fashion Feed",
        items=paginated,
        has_partial_content=False,
        total_items=total,
    )


# ---------------------------------------------------------------------------
# Content Lookup & Save Interaction (Section 6.28 & 6.29)
# ---------------------------------------------------------------------------

def get_fashion_content(content_type: FashionContentType, content_id: str) -> Any | None:
    """Lookup content item across domain repositories."""
    type_map: dict[FashionContentType, list[Any]] = {
        FashionContentType.PRODUCT: SAMPLE_PRODUCTS,
        FashionContentType.LOOK: SAMPLE_LOOKS,
        FashionContentType.OUTFIT: SAMPLE_OUTFITS,
        FashionContentType.COLLECTION: SAMPLE_COLLECTIONS,
        FashionContentType.STYLE: SAMPLE_STYLES,
        FashionContentType.TREND: SAMPLE_TRENDS,
        FashionContentType.BRAND: SAMPLE_BRANDS,
        FashionContentType.STORY: SAMPLE_STORIES,
        FashionContentType.RECOMMENDATION: SAMPLE_RECOMMENDATIONS,
    }

    bucket = type_map.get(content_type, [])
    for item in bucket:
        if getattr(item, "id", None) == content_id:
            return item
    return None


def toggle_content_save(
    content_type: FashionContentType,
    content_id: str,
    current_saved: bool,
) -> SaveToggleResultContract:
    """Execute save/unsave interaction with deterministic state machine (Section 6.29)."""
    new_saved_state = not current_saved
    return SaveToggleResultContract(
        content_id=content_id,
        content_type=content_type,
        is_saved=new_saved_state,
        state=SaveState.SAVED if new_saved_state else SaveState.UNSAVED,
        message=f"{str(content_type).capitalize()} {'saved to your wardrobe' if new_saved_state else 'removed from your wardrobe'}.",
    )


# ---------------------------------------------------------------------------
# Template Builders (Section 6.35 - 6.40)
# ---------------------------------------------------------------------------

def get_discovery_template() -> DiscoveryTemplateSpecContract:
    """Build the mixed discovery surface template spec (Section 6.40)."""
    return DiscoveryTemplateSpecContract(
        featured_story=SAMPLE_STORIES[0] if SAMPLE_STORIES else None,
        trending_items=SAMPLE_TRENDS,
        curated_collections=SAMPLE_COLLECTIONS,
        recommended_products=SAMPLE_RECOMMENDATIONS,
        featured_brands=SAMPLE_BRANDS,
    )


def get_listing_template(category: str = "all") -> ListingTemplateSpecContract:
    """Build a listing template spec for products/looks (Section 6.36)."""
    feed = get_fashion_feed(page=1, limit=20)
    return ListingTemplateSpecContract(
        title=f"Explore {category.capitalize()}",
        active_filters_count=0,
        sort_options=["Relevance", "Newest", "Price: Low to High", "Popularity"],
        selected_sort="Relevance",
        items=feed.items,
        total_count=feed.total_items,
        current_page=1,
        total_pages=1,
    )
