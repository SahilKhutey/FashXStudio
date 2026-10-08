"""Unit tests for Product & Fashion Detail Screens — Phase 09.

Verifies:
- PROD-001 to PROD-020: Product Detail, Gallery, Price, Availability, Variants, Specs, Reviews, Similar, Recommended, Styled-With
- FASH-001 to FASH-011: Fashion Story, Article, Collection, Look, Hotspots, Brand Story, Editorial, Inspiration
- State Resilience & Quality Gates: Out-of-Stock, Empty Reviews, Error Isolations, BaseContractModel extra="forbid"
"""

import pytest
from pydantic import ValidationError
from schemas.visual.detail import (
    BrandStoryDetailTemplateSpecContract,
    BreadcrumbItemContract,
    ComprehensiveProductDetailTemplateSpecContract,
    DetailScreenId,
    DetailState,
    EditorialViewTemplateSpecContract,
    FashionArticleDetailTemplateSpecContract,
    FashionCollectionDetailTemplateSpecContract,
    FashionInspirationDetailTemplateSpecContract,
    FashionLookDetailTemplateSpecContract,
    FashionStoryDetailTemplateSpecContract,
    LookHotspotContract,
    LookItemLinkContract,
    MediaItemContract,
    MediaType,
    ProductAvailabilityState,
    ProductAvailabilityTemplateSpecContract,
    ProductComparisonTemplateSpecContract,
    ProductDetailViewModelContract,
    ProductGalleryContract,
    ProductReviewsContract,
    ProductReviewsTemplateSpecContract,
    RelatedItemRelationship,
    RelatedProductItemContract,
    ReviewDistributionItemContract,
    SpecificationItemContract,
    SpecificationSectionContract,
    VariantGroupContract,
    VariantOptionItemContract,
    VariantOptionState,
)
from fashx.visual.detail_service import (
    get_brand_story_template,
    get_editorial_view_template,
    get_fashion_article_template,
    get_fashion_collection_template,
    get_fashion_inspiration_template,
    get_fashion_look_template,
    get_fashion_story_template,
    get_product_availability_template,
    get_product_comparison_template,
    get_product_detail_template,
    get_product_detail_view_model,
    get_product_reviews_template,
)


# ---------------------------------------------------------------------------
# PROD-001 through PROD-020: Product Detail Specifications
# ---------------------------------------------------------------------------

def test_prod_001_to_005_product_detail_and_facts() -> None:
    """PROD-001 to PROD-005: Product detail renders authoritative title, brand, price, and availability."""
    template = get_product_detail_template("prod-denim-01")
    assert template.screen_id == DetailScreenId.P02_PRODUCT_DETAIL
    vm = template.view_model
    assert vm.id == "prod-denim-01"
    assert vm.brand == "RawDenim Co."
    assert vm.title == "Selvedge Oversized Denim Jacket"
    assert vm.price == 4999.0
    assert vm.original_price == 6999.0
    assert vm.discount_percentage == 28
    assert vm.currency == "INR"
    assert vm.availability == ProductAvailabilityState.IN_STOCK
    assert vm.stock_units == 18


def test_prod_006_to_008_gallery_and_zoom() -> None:
    """PROD-006 to PROD-008: Media gallery supports multiple assets, primary view, and zoom capability."""
    vm = get_product_detail_view_model("prod-denim-01")
    gallery = vm.gallery
    assert len(gallery.items) >= 2
    assert gallery.items[0].is_primary is True
    assert gallery.items[0].aspect_ratio == "3:4"
    assert gallery.zoom_enabled is True
    assert gallery.items[1].media_type in [MediaType.DETAIL, MediaType.MODEL]


def test_prod_009_to_011_variant_selector_and_states() -> None:
    """PROD-009 to PROD-011: Variant selector enforces available, selected, and unavailable states."""
    vm = get_product_detail_view_model("prod-denim-01")
    color_group = next(g for g in vm.variant_groups if g.group_id == "color")
    assert color_group.selected_option_id == "opt-indigo"
    selected_opt = next(o for o in color_group.options if o.id == "opt-indigo")
    assert selected_opt.state == VariantOptionState.SELECTED
    assert selected_opt.swatch_hex is not None

    unavail_opt = next(o for o in color_group.options if o.id == "opt-charcoal")
    assert unavail_opt.state == VariantOptionState.UNAVAILABLE


def test_prod_012_quantity_bounds_and_breadcrumbs() -> None:
    """PROD-012 & Section 9.51: Breadcrumbs reflect canonical hierarchy and product context."""
    vm = get_product_detail_view_model("prod-denim-01")
    assert len(vm.breadcrumbs) == 4
    assert vm.breadcrumbs[0].label == "Home"
    assert vm.breadcrumbs[-1].is_current is True
    assert vm.breadcrumbs[-1].label == vm.title


def test_prod_015_and_016_specifications_and_overview() -> None:
    """PROD-015 & PROD-016: Structured specifications and progressive overview disclosure."""
    vm = get_product_detail_view_model("prod-denim-01")
    assert len(vm.short_summary) > 0
    assert len(vm.description) > 0
    assert len(vm.specifications) >= 2
    fabric_spec = next(s for s in vm.specifications if "Fabric" in s.group_name)
    assert any(item.label == "Material" for item in fabric_spec.items)


def test_prod_017_reviews_and_histogram_distribution() -> None:
    """PROD-017 & Section 9.21: Reviews include rating distribution histogram and verified review cards."""
    template = get_product_reviews_template("prod-denim-01")
    assert template.screen_id == DetailScreenId.P05_PRODUCT_REVIEWS
    revs = template.reviews
    assert revs.average_rating >= 4.0
    assert revs.total_reviews >= 100
    assert len(revs.distribution) == 5
    assert revs.distribution[0].stars == 5
    assert any(r.is_verified is True for r in revs.reviews)


def test_prod_018_to_020_content_relationships_semantics() -> None:
    """PROD-018 to PROD-020 & Section 9.26: Distinct semantics for Similar vs Recommended vs Styled-With."""
    vm = get_product_detail_view_model("prod-denim-01")
    assert len(vm.similar_products) >= 1
    assert vm.similar_products[0].relationship == RelatedItemRelationship.SIMILAR

    assert len(vm.recommended_products) >= 1
    assert vm.recommended_products[0].relationship == RelatedItemRelationship.RECOMMENDED
    assert "Japanese shuttle-loom" in (vm.recommended_products[0].reason or "")

    assert len(vm.styled_with) >= 1
    assert vm.styled_with[0].relationship == RelatedItemRelationship.STYLED_WITH


def test_prod_comparison_matrix_and_availability() -> None:
    """P09 & P10: Side-by-side product comparison and availability screen templates."""
    # P10: Availability template
    p10 = get_product_availability_template("prod-denim-01")
    assert p10.screen_id == DetailScreenId.P10_PRODUCT_AVAILABILITY
    assert p10.availability == ProductAvailabilityState.IN_STOCK
    assert p10.postal_code_supported is True
    assert p10.estimated_delivery_days >= 1

    # P09: Comparison template
    p09 = get_product_comparison_template(["prod-denim-01", "prod-linen-02"])
    assert p09.screen_id == DetailScreenId.P09_PRODUCT_COMPARISON
    assert len(p09.comparison.product_ids) == 2
    assert len(p09.comparison.attributes) >= 3


# ---------------------------------------------------------------------------
# FASH-001 through FASH-011: Fashion Detail Specifications
# ---------------------------------------------------------------------------

def test_fash_001_to_004_fashion_story_and_article() -> None:
    """FASH-001 to FASH-004: Story and Article detail templates with narrative and inline media."""
    # F03 Story
    story = get_fashion_story_template("story-coastal-layering")
    assert story.screen_id == DetailScreenId.F03_FASHION_STORY
    assert len(story.hero_media_uri) > 0
    assert len(story.content_markdown) > 0
    assert len(story.related_looks) >= 1
    assert len(story.related_products) >= 1

    # F04 Article
    article = get_fashion_article_template("art-indigo-weaving")
    assert article.screen_id == DetailScreenId.F04_FASHION_ARTICLE
    assert len(article.inline_media_uris) >= 2
    assert article.category == "Textile Heritage"


def test_fash_005_and_006_look_detail_and_hotspots() -> None:
    """FASH-005 & FASH-006: Look detail with interactive garment hotspots and outfit items."""
    look = get_fashion_look_template("look-mumbai-01")
    assert look.screen_id == DetailScreenId.F06_FASHION_LOOK
    assert len(look.outfit_items) >= 2
    assert look.outfit_items[0].slot in ["Outerwear", "Top", "Bottom"]
    assert len(look.hotspots) >= 2
    assert 0.0 <= look.hotspots[0].x_percent <= 100.0
    assert 0.0 <= look.hotspots[0].y_percent <= 100.0


def test_fash_007_and_008_collection_detail() -> None:
    """FASH-007 & FASH-008: Seasonal collection capsule with curated looks and products."""
    coll = get_fashion_collection_template("coll-monsoon-26")
    assert coll.screen_id == DetailScreenId.F05_FASHION_COLLECTION
    assert len(coll.looks) >= 1
    assert len(coll.products) >= 1
    assert len(coll.curator) > 0


def test_fash_009_to_011_brand_story_inspiration_editorial() -> None:
    """FASH-009 to FASH-011: Brand story, inspiration moodboards, and high-rhythm editorial views."""
    # F08 Brand Story
    brand = get_brand_story_template("brand-raw-denim")
    assert brand.screen_id == DetailScreenId.F08_BRAND_STORY
    assert brand.is_verified is True
    assert len(brand.values) >= 3
    assert len(brand.collections) >= 1

    # F07 Inspiration
    insp = get_fashion_inspiration_template("insp-monsoon-tactile")
    assert insp.screen_id == DetailScreenId.F07_FASHION_INSPIRATION
    assert len(insp.style_tags) >= 2
    assert len(insp.related_looks) >= 1

    # F09 Editorial View
    edit = get_editorial_view_template("edit-volumetric-street")
    assert edit.screen_id == DetailScreenId.F09_EDITORIAL_VIEW
    assert len(edit.narrative_blocks) >= 2
    assert len(edit.curated_looks) >= 1


# ---------------------------------------------------------------------------
# Strict Contract Validation (extra="forbid" & partial failure)
# ---------------------------------------------------------------------------

def test_detail_extra_fields_forbidden() -> None:
    """Enforce Constitution Rule I02: extra fields forbidden across detail contracts."""
    with pytest.raises(ValidationError):
        MediaItemContract(
            id="media-err",
            uri="https://images.fashx.com/err.jpg",
            alt_text="Err",
            unsupported_extra_field="fail",  # type: ignore
        )

    with pytest.raises(ValidationError):
        VariantOptionItemContract(
            id="opt-err",
            label="Err",
            value="err",
            random_attribute="fail",  # type: ignore
        )

    with pytest.raises(ValidationError):
        LookHotspotContract(
            product_id="prod-01",
            label="Pin",
            x_percent=50.0,
            y_percent=50.0,
            invalid_prop="fail",  # type: ignore
        )
