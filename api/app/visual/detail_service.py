"""Product & Fashion Detail Screens Domain Service — Phase 09.

Provides domain models, view model resolvers, media galleries, variant dependency engines,
review histograms, content relationship mappers, and screen templates for P02-P10 and F03-F09 (Sections 9.1-9.83).
"""

from typing import Any
from schemas.visual.fashion import (
    FashionContentType,
    VisualContentModel,
)
from schemas.visual.detail import (
    AttributeComparisonItemContract,
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
    ProductComparisonDetailContract,
    ProductComparisonTemplateSpecContract,
    ProductDetailViewModelContract,
    ProductGalleryContract,
    ProductReviewItemContract,
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
from .fashion_service import (
    SAMPLE_BRANDS,
    SAMPLE_COLLECTIONS,
    SAMPLE_LOOKS,
    SAMPLE_PRODUCTS,
    SAMPLE_STORIES,
    SAMPLE_STYLES,
    SAMPLE_TRENDS,
    to_visual_content_model,
)


# ---------------------------------------------------------------------------
# Product Detail Resolvers (P02, P03, P04, P05, P06, P07, P08, P09, P10)
# ---------------------------------------------------------------------------

def get_product_detail_view_model(product_id: str) -> ProductDetailViewModelContract:
    """Build authoritative, decoupled ProductDetailViewModelContract (Section 9.62)."""
    # Find matching product from sample products or default
    prod = next((p for p in SAMPLE_PRODUCTS if p.id == product_id), None)
    if not prod:
        prod = SAMPLE_PRODUCTS[0]

    # Gallery assets (Section 9.6 & 9.7)
    gallery_items: list[MediaItemContract] = [
        MediaItemContract(
            id=f"{prod.id}-img-primary",
            uri=prod.primary_image_uri,
            media_type=MediaType.IMAGE,
            alt_text=f"{prod.title} front studio view",
            aspect_ratio="3:4",
            is_primary=True,
            order=0,
        ),
    ]
    for idx, alt_uri in enumerate(prod.alternate_image_uris):
        mtype = MediaType.DETAIL if idx == 0 else MediaType.MODEL
        gallery_items.append(
            MediaItemContract(
                id=f"{prod.id}-img-alt-{idx+1}",
                uri=alt_uri,
                media_type=mtype,
                alt_text=f"{prod.title} detail angle {idx+1}",
                aspect_ratio="3:4",
                is_primary=False,
                order=idx + 1,
            )
        )

    # Variant groups with cross-option states (Section 9.12 & 9.14)
    variant_groups: list[VariantGroupContract] = [
        VariantGroupContract(
            group_id="color",
            name="Color",
            options=[
                VariantOptionItemContract(
                    id="opt-indigo",
                    label="Raw Indigo",
                    value="raw_indigo",
                    state=VariantOptionState.SELECTED,
                    swatch_hex="#1a2b4c",
                ),
                VariantOptionItemContract(
                    id="opt-washed",
                    label="Washed Blue",
                    value="washed_blue",
                    state=VariantOptionState.AVAILABLE,
                    swatch_hex="#4a6984",
                ),
                VariantOptionItemContract(
                    id="opt-charcoal",
                    label="Overdye Charcoal",
                    value="charcoal",
                    state=VariantOptionState.UNAVAILABLE,
                    swatch_hex="#222222",
                ),
            ],
            selected_option_id="opt-indigo",
        ),
        VariantGroupContract(
            group_id="size",
            name="Size",
            options=[
                VariantOptionItemContract(id="opt-s", label="S", value="S", state=VariantOptionState.AVAILABLE),
                VariantOptionItemContract(id="opt-m", label="M", value="M", state=VariantOptionState.SELECTED),
                VariantOptionItemContract(id="opt-l", label="L", value="L", state=VariantOptionState.AVAILABLE),
                VariantOptionItemContract(id="opt-xl", label="XL", value="XL", state=VariantOptionState.UNAVAILABLE),
            ],
            selected_option_id="opt-m",
        ),
    ]

    # Technical specifications (Section 9.19 & 9.20)
    specifications: list[SpecificationSectionContract] = [
        SpecificationSectionContract(
            group_name="Fabric & Construction",
            items=[
                SpecificationItemContract(label="Material", value=prod.attributes.get("fabric", "100% Cotton")),
                SpecificationItemContract(label="Weave", value="Shuttle-Loom Selvedge"),
                SpecificationItemContract(label="Dye Method", value="Natural Plant Indigo"),
            ],
        ),
        SpecificationSectionContract(
            group_name="Fit & Silhouette",
            items=[
                SpecificationItemContract(label="Fit Profile", value=prod.attributes.get("fit", "Relaxed Boxy")),
                SpecificationItemContract(label="Collar / Neck", value=prod.attributes.get("collar", "Spread Classic")),
                SpecificationItemContract(label="Length", value="Cropped Waist"),
            ],
        ),
        SpecificationSectionContract(
            group_name="Origin & Care",
            items=[
                SpecificationItemContract(label="Manufacturing Origin", value=prod.attributes.get("origin", "Kojima, Japan")),
                SpecificationItemContract(label="Care Instructions", value="Machine wash cold inside out, hang dry in shade"),
            ],
        ),
    ]

    # Review histogram & sample verified reviews (Section 9.21 - 9.23)
    reviews_spec = ProductReviewsContract(
        average_rating=prod.rating.value,
        total_reviews=prod.rating.rating_count,
        distribution=[
            ReviewDistributionItemContract(stars=5, count=95, percentage=66.9),
            ReviewDistributionItemContract(stars=4, count=36, percentage=25.4),
            ReviewDistributionItemContract(stars=3, count=8, percentage=5.6),
            ReviewDistributionItemContract(stars=2, count=2, percentage=1.4),
            ReviewDistributionItemContract(stars=1, count=1, percentage=0.7),
        ],
        reviews=[
            ProductReviewItemContract(
                id="rev-01",
                author="Vikram S.",
                rating=5,
                date="2026-09-18",
                comment="Exceptional 14oz drape. The boxy cut sits perfectly over linen shirts in humid weather.",
                is_verified=True,
                helpful_count=24,
            ),
            ProductReviewItemContract(
                id="rev-02",
                author="Ananya M.",
                rating=4,
                date="2026-09-10",
                comment="True artisanal selvedge with beautiful pink ID line. Stiff initially but breaks in gracefully.",
                is_verified=True,
                helpful_count=12,
            ),
        ],
        state=DetailState.READY,
    )

    # Content relationships (Section 9.24 - 9.27)
    similar_products: list[RelatedProductItemContract] = [
        RelatedProductItemContract(
            relationship=RelatedItemRelationship.SIMILAR,
            product_id="prod-linen-02",
            title="Relaxed Camp Collar Linen Shirt",
            brand="Breeze & Loom",
            image_uri="https://images.fashx.com/products/linen_shirt_sand.jpg",
            price=2499.0,
            original_price=None,
            reason="Similar breathable natural fiber and relaxed boxy tailoring.",
        ),
    ]

    recommended_products: list[RelatedProductItemContract] = [
        RelatedProductItemContract(
            relationship=RelatedItemRelationship.RECOMMENDED,
            product_id="prod-denim-01",
            title="Selvedge Oversized Denim Jacket",
            brand="RawDenim Co.",
            image_uri="https://images.fashx.com/products/denim_jacket_front.jpg",
            price=4999.0,
            original_price=6999.0,
            reason="Matches your explored preferences for Japanese shuttle-loom denim.",
        ),
    ]

    styled_with: list[RelatedProductItemContract] = [
        RelatedProductItemContract(
            relationship=RelatedItemRelationship.STYLED_WITH,
            product_id="prod-linen-02",
            title="Relaxed Camp Collar Linen Shirt",
            brand="Breeze & Loom",
            image_uri="https://images.fashx.com/products/linen_shirt_sand.jpg",
            price=2499.0,
            original_price=None,
            reason="Featured ensemble piece in Bandra Sunday Street Look.",
        ),
    ]

    # Breadcrumbs (Section 9.51)
    breadcrumbs: list[BreadcrumbItemContract] = [
        BreadcrumbItemContract(label="Home", route="/"),
        BreadcrumbItemContract(label="Catalog", route="/explore/products"),
        BreadcrumbItemContract(label=prod.category, route=f"/explore/products?category={prod.category.lower()}"),
        BreadcrumbItemContract(label=prod.title, route=f"/products/{prod.id}", is_current=True),
    ]

    return ProductDetailViewModelContract(
        id=prod.id,
        brand=prod.brand,
        title=prod.title,
        price=prod.price.amount,
        original_price=prod.price.original_amount,
        currency="INR",
        discount_percentage=prod.price.discount_percentage,
        rating=prod.rating.value,
        review_count=prod.rating.rating_count,
        availability=ProductAvailabilityState.IN_STOCK if prod.is_in_stock else ProductAvailabilityState.OUT_OF_STOCK,
        stock_units=18 if prod.is_in_stock else 0,
        short_summary="Artisanal shuttle-loom garment crafted with Japanese selvedge denim and natural plant dyes.",
        description="A masterclass in contemporary silhouettes meets heritage textile mills. Features reinforced pocket seams, heavy-gauge stitching, and custom brass hardware engineered for enduring wear.",
        gallery=ProductGalleryContract(items=gallery_items, active_index=0, zoom_enabled=True),
        variant_groups=variant_groups,
        specifications=specifications,
        reviews=reviews_spec,
        similar_products=similar_products,
        recommended_products=recommended_products,
        styled_with=styled_with,
        breadcrumbs=breadcrumbs,
        state=DetailState.READY,
    )


def get_product_detail_template(product_id: str) -> ComprehensiveProductDetailTemplateSpecContract:
    """Build P02 Product Detail screen template specification (Section 9.4, 9.60)."""
    view_model = get_product_detail_view_model(product_id=product_id)
    return ComprehensiveProductDetailTemplateSpecContract(
        screen_id=DetailScreenId.P02_PRODUCT_DETAIL,
        view_model=view_model,
    )


def get_product_reviews_template(product_id: str) -> ProductReviewsTemplateSpecContract:
    """Build P05 dedicated Product Reviews screen template specification (Section 9.21, 9.60)."""
    vm = get_product_detail_view_model(product_id=product_id)
    return ProductReviewsTemplateSpecContract(
        screen_id=DetailScreenId.P05_PRODUCT_REVIEWS,
        product_id=product_id,
        reviews=vm.reviews,
    )


def get_product_availability_template(product_id: str) -> ProductAvailabilityTemplateSpecContract:
    """Build P10 detailed Product Availability & Logistics template (Section 9.11, 9.60)."""
    vm = get_product_detail_view_model(product_id=product_id)
    return ProductAvailabilityTemplateSpecContract(
        screen_id=DetailScreenId.P10_PRODUCT_AVAILABILITY,
        product_id=product_id,
        availability=vm.availability,
        stock_units=vm.stock_units,
        estimated_delivery_days=3,
        postal_code_supported=True,
        shipping_origin="Mumbai Central Fulfillment Center",
    )


def get_product_comparison_template(product_ids: list[str]) -> ProductComparisonTemplateSpecContract:
    """Build P09 side-by-side product comparison template specification (Section 9.31, 9.60)."""
    products_data: list[dict[str, Any]] = []
    for pid in product_ids:
        vm = get_product_detail_view_model(pid)
        products_data.append({
            "id": vm.id,
            "title": vm.title,
            "brand": vm.brand,
            "price": vm.price,
            "availability": vm.availability,
            "rating": vm.rating,
        })

    attributes: list[AttributeComparisonItemContract] = [
        AttributeComparisonItemContract(
            attribute_name="Price",
            values={p["id"]: f"₹{p['price']:,.2f}" for p in products_data},
        ),
        AttributeComparisonItemContract(
            attribute_name="Brand",
            values={p["id"]: p["brand"] for p in products_data},
        ),
        AttributeComparisonItemContract(
            attribute_name="Availability",
            values={p["id"]: p["availability"].replace("_", " ").title() for p in products_data},
        ),
        AttributeComparisonItemContract(
            attribute_name="Customer Rating",
            values={p["id"]: f"{p['rating']} ★" for p in products_data},
        ),
    ]

    return ProductComparisonTemplateSpecContract(
        screen_id=DetailScreenId.P09_PRODUCT_COMPARISON,
        comparison=ProductComparisonDetailContract(
            product_ids=product_ids,
            products=products_data,
            attributes=attributes,
        ),
    )


# ---------------------------------------------------------------------------
# Fashion Detail Resolvers (F03, F04, F05, F06, F07, F08, F09)
# ---------------------------------------------------------------------------

def get_fashion_story_template(story_id: str) -> FashionStoryDetailTemplateSpecContract:
    """Build F03 Fashion Story template specification (Section 9.34)."""
    story = next((s for s in SAMPLE_STORIES if s.id == story_id), SAMPLE_STORIES[0])
    return FashionStoryDetailTemplateSpecContract(
        screen_id=DetailScreenId.F03_FASHION_STORY,
        id=story.id,
        title=story.title,
        subtitle=story.subtitle,
        author=story.author,
        published_date=story.published_date,
        category=story.category,
        hero_media_uri=story.hero_image_uri,
        content_markdown=story.content_markdown,
        related_looks=[to_visual_content_model(l, FashionContentType.LOOK) for l in SAMPLE_LOOKS[:2]],
        related_products=[to_visual_content_model(p, FashionContentType.PRODUCT) for p in SAMPLE_PRODUCTS[:2]],
        state=DetailState.READY,
    )


def get_fashion_article_template(article_id: str) -> FashionArticleDetailTemplateSpecContract:
    """Build F04 Fashion Article template specification (Section 9.35)."""
    return FashionArticleDetailTemplateSpecContract(
        screen_id=DetailScreenId.F04_FASHION_ARTICLE,
        id=article_id,
        category="Textile Heritage",
        title="Weaving Sovereignty: The Indigo Mills of Kojima and Kutch",
        subtitle="A historical exploration of plant-based indigo dyeing across Japanese and Indian artisanal clusters.",
        author="Rohit Verma, Senior Textile Historian",
        published_date="2026-09-22",
        hero_media_uri="https://images.fashx.com/stories/indigo_heritage.jpg",
        body_markdown="True selvedge denim does not simply resist abrasion; it records the physical history of its wearer...",
        inline_media_uris=[
            "https://images.fashx.com/stories/indigo_vat_detail.jpg",
            "https://images.fashx.com/stories/handloom_shuttle.jpg",
        ],
        related_products=[to_visual_content_model(p, FashionContentType.PRODUCT) for p in SAMPLE_PRODUCTS],
        state=DetailState.READY,
    )


def get_fashion_collection_template(collection_id: str) -> FashionCollectionDetailTemplateSpecContract:
    """Build F05 Fashion Collection template specification (Section 9.40)."""
    coll = next((c for c in SAMPLE_COLLECTIONS if c.id == collection_id), SAMPLE_COLLECTIONS[0])
    return FashionCollectionDetailTemplateSpecContract(
        screen_id=DetailScreenId.F05_FASHION_COLLECTION,
        id=coll.id,
        name=coll.title,
        season="Monsoon / Transitional 2026",
        description=coll.description,
        curator="FashXStudio Curatorial Guild",
        hero_image_uri=coll.hero_image_uri,
        looks=[to_visual_content_model(l, FashionContentType.LOOK) for l in SAMPLE_LOOKS],
        products=[to_visual_content_model(p, FashionContentType.PRODUCT) for p in SAMPLE_PRODUCTS],
        styles=[to_visual_content_model(s, FashionContentType.STYLE) for s in SAMPLE_STYLES],
        related_collections=[to_visual_content_model(c, FashionContentType.COLLECTION) for c in SAMPLE_COLLECTIONS],
        state=DetailState.READY,
    )


def get_fashion_look_template(look_id: str) -> FashionLookDetailTemplateSpecContract:
    """Build F06 Fashion Look template with interactive item mapping and hotspots (Section 9.37 - 9.39)."""
    look = next((l for l in SAMPLE_LOOKS if l.id == look_id), SAMPLE_LOOKS[0])
    outfit_items: list[LookItemLinkContract] = [
        LookItemLinkContract(
            slot="Outerwear",
            product_id="prod-denim-01",
            title="Selvedge Oversized Denim Jacket",
            brand="RawDenim Co.",
            price=4999.0,
            image_uri="https://images.fashx.com/products/denim_jacket_front.jpg",
        ),
        LookItemLinkContract(
            slot="Top",
            product_id="prod-linen-02",
            title="Relaxed Camp Collar Linen Shirt",
            brand="Breeze & Loom",
            price=2499.0,
            image_uri="https://images.fashx.com/products/linen_shirt_sand.jpg",
        ),
    ]

    hotspots: list[LookHotspotContract] = [
        LookHotspotContract(product_id="prod-denim-01", label="Denim Jacket", x_percent=50.0, y_percent=32.0),
        LookHotspotContract(product_id="prod-linen-02", label="Linen Shirt", x_percent=48.0, y_percent=52.0),
    ]

    return FashionLookDetailTemplateSpecContract(
        screen_id=DetailScreenId.F06_FASHION_LOOK,
        id=look.id,
        name=look.title,
        style="Contemporary Streetwear",
        context_description=f"Curated streetwear look set against coastal architectural landscapes.",
        hero_image_uri=look.hero_image_uri,
        outfit_items=outfit_items,
        hotspots=hotspots,
        related_looks=[to_visual_content_model(l, FashionContentType.LOOK) for l in SAMPLE_LOOKS],
        is_saved=False,
        state=DetailState.READY,
    )


def get_fashion_inspiration_template(inspiration_id: str) -> FashionInspirationDetailTemplateSpecContract:
    """Build F07 Fashion Inspiration template specification (Section 9.43)."""
    return FashionInspirationDetailTemplateSpecContract(
        screen_id=DetailScreenId.F07_FASHION_INSPIRATION,
        id=inspiration_id,
        title="Tactile Monsoons: Waterproof Waxed Cottons & Breathable Linens",
        context="Editorial moodboard curated from street photography in South Mumbai and Tokyo.",
        media_uri="https://images.fashx.com/inspiration/moodboard_monsoon.jpg",
        style_tags=["High-Humidity Tailoring", "Waxed Cotton", "Flax Linen", "Indigo Hues"],
        related_looks=[to_visual_content_model(l, FashionContentType.LOOK) for l in SAMPLE_LOOKS],
        related_products=[to_visual_content_model(p, FashionContentType.PRODUCT) for p in SAMPLE_PRODUCTS],
        is_saved=True,
        state=DetailState.READY,
    )


def get_brand_story_template(brand_id: str) -> BrandStoryDetailTemplateSpecContract:
    """Build F08 Brand Story template specification (Section 9.42)."""
    brand = next((b for b in SAMPLE_BRANDS if b.id == brand_id), SAMPLE_BRANDS[0])
    return BrandStoryDetailTemplateSpecContract(
        screen_id=DetailScreenId.F08_BRAND_STORY,
        id=brand.id,
        brand_name=brand.name,
        hero_image_uri=brand.cover_image_uri,
        logo_uri=brand.logo_uri,
        story_markdown=f"{brand.name} was established with a singular ethos: revive artisanal shuttle looms and respect the raw rhythm of natural fibers. Every garment carries the signature of the craftsman.",
        values=["Zero Microplastics", "Fair Wage Certified Artisans", "Small Batch Runs", "Ancestral Dye Methods"],
        collections=[to_visual_content_model(c, FashionContentType.COLLECTION) for c in SAMPLE_COLLECTIONS],
        featured_products=[to_visual_content_model(p, FashionContentType.PRODUCT) for p in SAMPLE_PRODUCTS],
        featured_looks=[to_visual_content_model(l, FashionContentType.LOOK) for l in SAMPLE_LOOKS],
        is_verified=brand.is_verified,
        state=DetailState.READY,
    )


def get_editorial_view_template(editorial_id: str) -> EditorialViewTemplateSpecContract:
    """Build F09 Editorial View template with large visual rhythm (Section 9.36)."""
    return EditorialViewTemplateSpecContract(
        screen_id=DetailScreenId.F09_EDITORIAL_VIEW,
        id=editorial_id,
        title="The Geometry of Modern Streetwear: Volumetric Forms & Raw Textiles",
        hero_media_uri="https://images.fashx.com/editorial/volumetric_street.jpg",
        narrative_blocks=[
            {"type": "headline", "content": "Beyond Fast Fashion: The Permanence of Heavyweight Cottons"},
            {"type": "paragraph", "content": "Modern urban environments necessitate clothing that acts as modular armor rather than disposable ornament."},
            {"type": "pullquote", "content": "Fashion is architectural proportion applied to the moving human anatomy."},
        ],
        curated_looks=[to_visual_content_model(l, FashionContentType.LOOK) for l in SAMPLE_LOOKS],
        curated_products=[to_visual_content_model(p, FashionContentType.PRODUCT) for p in SAMPLE_PRODUCTS],
        state=DetailState.READY,
    )
