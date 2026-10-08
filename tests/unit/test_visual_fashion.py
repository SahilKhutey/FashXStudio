"""Unit tests for FashXStudio Fashion Content Design System — Phase 06.

Covers: FASH-001 through FASH-015 (Sections 6.1-6.62)
- Product: media hierarchy, price, attributes, save state
- Look & Outfit: styled composition, piece mapping slots (top, bottom, etc.)
- Collection & Style: season tag, aesthetic taxonomy
- Trend & Timeline: momentum signals, timeline points
- Brand & Story: identity preservation, editorial narrative
- Recommendation: AI explainability, confidence score, source transparency
- VisualContentModel: polymorphic adapter across content types
- Save State Machine: deterministic transitions
"""

import pytest
from schemas.visual.components import PriceSpecContract, RatingSpecContract
from schemas.visual.fashion import (
    BrandItemContract,
    CollectionItemContract,
    ContentSourceType,
    ContentState,
    FashionContentType,
    FashionFeedContract,
    FashionStoryContract,
    LookItemContract,
    ModerationState,
    OutfitItemContract,
    OutfitPieceMappingContract,
    ProductItemContract,
    RecommendationItemContract,
    SaveState,
    StyleCategoryContract,
    TrendItemContract,
    TrendMomentum,
    TrendSignalPointContract,
    VisualContentModel,
)
from fashx.visual.fashion_service import (
    get_discovery_template,
    get_fashion_content,
    get_fashion_feed,
    get_listing_template,
    to_visual_content_model,
    toggle_content_save,
)


# ---------------------------------------------------------------------------
# FASH-001 - FASH-004: Product Visual System
# ---------------------------------------------------------------------------

def test_fash_001_product_item_contract() -> None:
    """FASH-001: Product item contract validates title, brand, and media."""
    prod = ProductItemContract(
        id="prod-101",
        brand="Acne Studios",
        title="Oversized Wool Scarf",
        primary_image_uri="https://images.fashx.com/scarf.jpg",
        price=PriceSpecContract(amount=18000.0),
        category="Accessories",
    )
    assert prod.id == "prod-101"
    assert prod.brand == "Acne Studios"
    assert prod.category == "Accessories"
    assert prod.state == ContentState.LOADED
    assert prod.moderation_state == ModerationState.VISIBLE


def test_fash_002_product_media_alternate_images() -> None:
    """FASH-002: Product supports primary and alternate detail angles."""
    prod = ProductItemContract(
        id="prod-102",
        brand="Lemaire",
        title="Croissant Bag",
        primary_image_uri="https://images.fashx.com/bag_front.jpg",
        alternate_image_uris=[
            "https://images.fashx.com/bag_side.jpg",
            "https://images.fashx.com/bag_interior.jpg",
        ],
        price=PriceSpecContract(amount=85000.0),
        category="Bags",
    )
    assert len(prod.alternate_image_uris) == 2


def test_fash_003_product_price_and_discount() -> None:
    """FASH-003: Product price tracks current and strikethrough original."""
    prod = ProductItemContract(
        id="prod-103",
        brand="COS",
        title="Pleated Trousers",
        primary_image_uri="https://images.fashx.com/trousers.jpg",
        price=PriceSpecContract(amount=6990.0, original_amount=9990.0, discount_percentage=30),
        category="Bottoms",
    )
    assert prod.price.amount == 6990.0
    assert prod.price.discount_percentage == 30


def test_fash_004_product_extra_fields_forbidden() -> None:
    """FASH-004: Product contract strictly rejects undeclared fields (extra='forbid')."""
    with pytest.raises(Exception):
        ProductItemContract(
            id="p-fail",
            brand="Zara",
            title="Tee",
            primary_image_uri="https://images.fashx.com/tee.jpg",
            price=PriceSpecContract(amount=1490.0),
            category="Tops",
            arbitrary_custom_field=True,  # type: ignore
        )


# ---------------------------------------------------------------------------
# FASH-005 - FASH-007: Look, Outfit & Collection Systems
# ---------------------------------------------------------------------------

def test_fash_005_look_card_contract() -> None:
    """FASH-005: Look contract validates style name, piece count, and curator."""
    look = LookItemContract(
        id="look-01",
        title="Minimal Scandinavian Summer",
        style_name="Minimalist",
        hero_image_uri="https://images.fashx.com/scandi.jpg",
        items_count=3,
        associated_product_ids=["p-1", "p-2", "p-3"],
        curator_name="Elena Rostova",
    )
    assert look.items_count == 3
    assert look.style_name == "Minimalist"


def test_fash_006_outfit_piece_mapping() -> None:
    """FASH-006: Outfit contract associates constituent pieces by slot."""
    pieces = [
        OutfitPieceMappingContract(
            slot="outerwear",
            product_id="prod-jacket",
            product_title="Trench Coat",
            image_uri="https://images.fashx.com/trench.jpg",
            price=PriceSpecContract(amount=12999.0),
        ),
        OutfitPieceMappingContract(
            slot="shoes",
            product_id="prod-boots",
            product_title="Chelsea Boots",
            image_uri="https://images.fashx.com/boots.jpg",
            price=PriceSpecContract(amount=8999.0),
        ),
    ]
    outfit = OutfitItemContract(
        id="outfit-01",
        title="Autumn Rainy Day",
        image_uri="https://images.fashx.com/outfit_hero.jpg",
        pieces=pieces,
        total_price=PriceSpecContract(amount=21998.0),
    )
    assert len(outfit.pieces) == 2
    assert outfit.pieces[0].slot == "outerwear"
    assert outfit.total_price.amount == 21998.0


def test_fash_007_collection_contract() -> None:
    """FASH-007: Collection contract specifies hero, season tag, and item count."""
    coll = CollectionItemContract(
        id="coll-festive-26",
        title="Festive Silks & Handlooms",
        description="Handwoven Chanderi and Banarasi silks for autumnal celebrations.",
        hero_image_uri="https://images.fashx.com/festive_hero.jpg",
        item_count=42,
        season_tag="Festive 2026",
    )
    assert coll.item_count == 42
    assert coll.season_tag == "Festive 2026"


# ---------------------------------------------------------------------------
# FASH-008 - FASH-010: Style, Trend & Timeline Systems
# ---------------------------------------------------------------------------

def test_fash_008_style_category() -> None:
    """FASH-008: Style category tracks aesthetic definition and look tally."""
    style = StyleCategoryContract(
        id="style-boho",
        name="Bohemian Chic",
        description="Free-spirited silhouettes with artisanal embroideries.",
        image_uri="https://images.fashx.com/boho.jpg",
        look_count=64,
        associated_tags=["Fringe", "Maxi", "Florals"],
    )
    assert style.look_count == 64
    assert "Fringe" in style.associated_tags


def test_fash_009_trend_item_momentum() -> None:
    """FASH-009: Trend tracks momentum trajectory signals."""
    trend = TrendItemContract(
        id="trend-metallics",
        title="Liquid Metallics",
        category="Finishes",
        image_uri="https://images.fashx.com/metallics.jpg",
        momentum=TrendMomentum.PEAKING,
        regions=["Mumbai", "Delhi"],
    )
    assert trend.momentum == TrendMomentum.PEAKING
    assert len(trend.regions) == 2


def test_fash_010_trend_timeline_points() -> None:
    """FASH-010: Trend timeline records timestamped signal intensities."""
    pts = [
        TrendSignalPointContract(timestamp="2026-01", signal_label="Runway debut", intensity=0.2),
        TrendSignalPointContract(timestamp="2026-05", signal_label="Celebrity adoption", intensity=0.7),
        TrendSignalPointContract(timestamp="2026-09", signal_label="Mass retail peak", intensity=0.95),
    ]
    trend = TrendItemContract(
        id="trend-sheer",
        title="Sheer Layering",
        category="Textiles",
        image_uri="https://images.fashx.com/sheer.jpg",
        timeline=pts,
    )
    assert len(trend.timeline) == 3
    assert trend.timeline[-1].intensity == 0.95


# ---------------------------------------------------------------------------
# FASH-011 - FASH-013: Brand & Editorial Systems
# ---------------------------------------------------------------------------

def test_fash_011_brand_item() -> None:
    """FASH-011: Brand preserves brand identity, logo, and verified badge."""
    brand = BrandItemContract(
        id="brand-raw-mango",
        name="Raw Mango",
        logo_uri="https://images.fashx.com/rawmango_logo.png",
        category="Contemporary Handloom",
        product_count=86,
        is_verified=True,
    )
    assert brand.is_verified is True
    assert brand.product_count == 86


def test_fash_012_fashion_story_editorial() -> None:
    """FASH-012: Story contract captures author, date, and narrative content."""
    story = FashionStoryContract(
        id="story-khadi",
        title="Reimagining Khadi in Contemporary Tailoring",
        hero_image_uri="https://images.fashx.com/khadi_hero.jpg",
        author="Arjun Varma",
        published_date="2026-09-15",
        content_markdown="Handspun yarn meets structural architectural tailoring...",
        category="Artisanship",
        related_product_ids=["p-khadi-blazer"],
    )
    assert story.author == "Arjun Varma"
    assert len(story.related_product_ids) == 1


# ---------------------------------------------------------------------------
# FASH-014 - FASH-015: Recommendations & AI Transparency
# ---------------------------------------------------------------------------

def test_fash_014_recommendation_item_explainability() -> None:
    """FASH-014: Recommendation item requires explanation reason and confidence."""
    prod = ProductItemContract(
        id="p-linen",
        brand="Muji",
        title="Linen Band Collar Shirt",
        primary_image_uri="https://images.fashx.com/muji_linen.jpg",
        price=PriceSpecContract(amount=3290.0),
        category="Tops",
    )
    rec = RecommendationItemContract(
        id="rec-01",
        target_content_type=FashionContentType.PRODUCT,
        product=prod,
        explanation_reason="Recommended because you prefer breathable natural fabrics in high humidity.",
        confidence_score=0.91,
        source_type=ContentSourceType.AI_GENERATED,
    )
    assert "breathable natural fabrics" in rec.explanation_reason
    assert rec.confidence_score == 0.91
    assert rec.source_type == ContentSourceType.AI_GENERATED


def test_fash_015_recommendation_confidence_bounds() -> None:
    """FASH-015: Recommendation rejects confidence score outside [0.0, 1.0]."""
    prod = ProductItemContract(
        id="p-test",
        brand="Test",
        title="Test",
        primary_image_uri="https://images.fashx.com/test.jpg",
        price=PriceSpecContract(amount=100.0),
        category="Test",
    )
    with pytest.raises(Exception):
        RecommendationItemContract(
            id="rec-err",
            target_content_type=FashionContentType.PRODUCT,
            product=prod,
            explanation_reason="Reason",
            confidence_score=1.5,  # Out of bounds
        )


# ---------------------------------------------------------------------------
# VisualContentModel Polymorphic Adapter & Feed
# ---------------------------------------------------------------------------

def test_visual_content_model_adapter_product() -> None:
    """to_visual_content_model adapts Product to polymorphic VisualContentModel."""
    prod = ProductItemContract(
        id="p-1",
        brand="Fabindia",
        title="Cotton Kurta",
        primary_image_uri="https://images.fashx.com/kurta.jpg",
        price=PriceSpecContract(amount=1890.0),
        category="Kurtas",
    )
    model = to_visual_content_model(prod, FashionContentType.PRODUCT)
    assert model.id == "p-1"
    assert model.content_type == FashionContentType.PRODUCT
    assert model.subtitle == "Fabindia"
    assert model.price.amount == 1890.0


def test_fashion_feed_generator() -> None:
    """get_fashion_feed returns mixed-content discovery feed."""
    feed = get_fashion_feed(page=1, limit=5)
    assert isinstance(feed, FashionFeedContract)
    assert len(feed.items) <= 5
    assert feed.total_items > 0


# ---------------------------------------------------------------------------
# Save State Machine Interaction
# ---------------------------------------------------------------------------

def test_toggle_content_save_state_machine() -> None:
    """toggle_content_save toggles unsaved to saved, and saved to unsaved."""
    res_save = toggle_content_save(FashionContentType.PRODUCT, "p-1", current_saved=False)
    assert res_save.is_saved is True
    assert res_save.state == SaveState.SAVED

    res_unsave = toggle_content_save(FashionContentType.PRODUCT, "p-1", current_saved=True)
    assert res_unsave.is_saved is False
    assert res_unsave.state == SaveState.UNSAVED


# ---------------------------------------------------------------------------
# Template Builders
# ---------------------------------------------------------------------------

def test_discovery_template_builder() -> None:
    """get_discovery_template builds complete discovery spec with mixed content."""
    template = get_discovery_template()
    assert template.featured_story is not None
    assert len(template.trending_items) > 0
    assert len(template.curated_collections) > 0
    assert len(template.recommended_products) > 0


def test_listing_template_builder() -> None:
    """get_listing_template builds listing spec with sorting and items."""
    template = get_listing_template(category="outerwear")
    assert "Outerwear" in template.title
    assert len(template.sort_options) > 0
    assert len(template.items) > 0
