"""Discovery & Search Screens Domain Service — Phase 08.

Provides domain models, multi-type search engine, autocomplete suggestions,
module resolvers, and template specifications for FashXStudio discovery (Sections 8.1-8.82).
"""

from typing import Any
from schemas.visual.fashion import (
    FashionContentType,
    VisualContentModel,
)
from schemas.visual.shopping import (
    ActiveFilterContract,
    FilterStateContract,
    SortOption,
)
from schemas.visual.discovery import (
    AdvancedSearchCriteriaContract,
    AdvancedSearchTemplateSpecContract,
    DiscoveryHeroContract,
    DiscoveryHomeTemplateSpecContract,
    DiscoveryModuleActionContract,
    DiscoveryModuleContract,
    DiscoveryModuleType,
    DiscoveryResultsTemplateSpecContract,
    DiscoveryScreenId,
    DiscoveryState,
    DiscoveryViewModelContract,
    ExploreTemplateSpecContract,
    ExploreType,
    PersonalizedDiscoveryTemplateSpecContract,
    RecentSearchContract,
    SearchResultCountsContract,
    SearchResultsTemplateSpecContract as UnifiedSearchResultsTemplateSpecContract,
    SearchResultType,
    SearchHomeTemplateSpecContract,
    SearchSuggestionContract,
    SearchViewModelContract,
    SuggestionType,
)
from .fashion_service import (
    SAMPLE_BRANDS,
    SAMPLE_COLLECTIONS,
    SAMPLE_LOOKS,
    SAMPLE_PRODUCTS,
    SAMPLE_RECOMMENDATIONS,
    SAMPLE_STORIES,
    SAMPLE_STYLES,
    SAMPLE_TRENDS,
    to_visual_content_model,
)
from .shopping_service import SAMPLE_FILTER_GROUPS


# ---------------------------------------------------------------------------
# In-Memory Search History & Autocomplete Fixtures (Sections 8.16, 8.18, 8.20)
# ---------------------------------------------------------------------------

SAMPLE_RECENT_SEARCHES: list[RecentSearchContract] = [
    RecentSearchContract(query="linen shirts", timestamp="2026-10-01T09:30:00Z"),
    RecentSearchContract(query="streetwear", timestamp="2026-10-01T08:15:00Z"),
    RecentSearchContract(query="selvedge denim", timestamp="2026-09-30T18:45:00Z"),
]

TRENDING_SEARCH_KEYWORDS: list[str] = [
    "Raw Denim",
    "Camp Collar",
    "Liquid Metallics",
    "Chanderi Silk",
    "Monsoon Layering",
    "Bandra Streetwear",
]

SAMPLE_SUGGESTIONS_CATALOG: list[SearchSuggestionContract] = [
    SearchSuggestionContract(text="linen shirts", suggestion_type=SuggestionType.QUERY, count=45),
    SearchSuggestionContract(text="linen camp collar shirt", suggestion_type=SuggestionType.PRODUCT, target_id="prod-linen-02"),
    SearchSuggestionContract(text="RawDenim Co.", suggestion_type=SuggestionType.BRAND, target_id="brand-raw-denim"),
    SearchSuggestionContract(text="Contemporary Streetwear", suggestion_type=SuggestionType.STYLE, target_id="style-streetwear"),
    SearchSuggestionContract(text="Unfinished Raw Textures", suggestion_type=SuggestionType.TREND, target_id="trend-raw-textures"),
    SearchSuggestionContract(text="Outerwear", suggestion_type=SuggestionType.CATEGORY, count=18),
    SearchSuggestionContract(text="selvedge oversized denim jacket", suggestion_type=SuggestionType.PRODUCT, target_id="prod-denim-01"),
]


# ---------------------------------------------------------------------------
# Discovery Hero & Module Builders (Sections 8.5, 8.6, 8.34 - 8.39)
# ---------------------------------------------------------------------------

def get_discovery_hero() -> DiscoveryHeroContract:
    """Build the primary Discovery Hero banner (Section 8.6)."""
    return DiscoveryHeroContract(
        id="hero-monsoon-26",
        title="Monsoon Transitional '26",
        subtitle="Explore hydrophobic natural fibers, breathable linen weaves, and architectural streetwear.",
        media_uri="https://images.fashx.com/collections/monsoon_hero.jpg",
        primary_action_label="Explore Collection",
        primary_action_route="/explore/collections/coll-monsoon-26",
        secondary_action_label="View Lookbook",
        secondary_action_route="/explore/looks/look-mumbai-01",
    )


def build_discovery_modules() -> list[DiscoveryModuleContract]:
    """Assemble heterogeneous discovery modules for feed rendering (Section 8.34)."""
    modules: list[DiscoveryModuleContract] = []

    # 1. Editorial Story Module
    story_items = [to_visual_content_model(s, FashionContentType.STORY) for s in SAMPLE_STORIES]
    modules.append(
        DiscoveryModuleContract(
            id="mod-editorial",
            module_type=DiscoveryModuleType.EDITORIAL_STORY,
            title="Fashion Dispatches",
            description="Deep dives into contemporary subcultures, textiles, and silhouettes.",
            items=story_items,
            action=DiscoveryModuleActionContract(label="Read More", route="/explore/fashion"),
            priority=1,
            visibility=True,
            state=DiscoveryState.READY,
        )
    )

    # 2. Trending Products Module
    product_items = [to_visual_content_model(p, FashionContentType.PRODUCT) for p in SAMPLE_PRODUCTS]
    modules.append(
        DiscoveryModuleContract(
            id="mod-trending-products",
            module_type=DiscoveryModuleType.TRENDING_PRODUCTS,
            title="Trending in Apparel",
            description="Most engaged and curated pieces across our merchant collective.",
            items=product_items,
            action=DiscoveryModuleActionContract(label="View All", route="/explore/products"),
            priority=2,
            visibility=True,
            state=DiscoveryState.READY,
        )
    )

    # 3. Recommended Looks Module
    look_items = [to_visual_content_model(l, FashionContentType.LOOK) for l in SAMPLE_LOOKS]
    modules.append(
        DiscoveryModuleContract(
            id="mod-recommended-looks",
            module_type=DiscoveryModuleType.RECOMMENDED_LOOKS,
            title="Curated Street Looks",
            description="Complete styled compositions curated by leading stylists.",
            items=look_items,
            action=DiscoveryModuleActionContract(label="Explore Looks", route="/explore/looks"),
            priority=3,
            visibility=True,
            state=DiscoveryState.READY,
        )
    )

    # 4. Regional Trends Module
    trend_items = [to_visual_content_model(t, FashionContentType.TREND) for t in SAMPLE_TRENDS]
    modules.append(
        DiscoveryModuleContract(
            id="mod-regional-trends",
            module_type=DiscoveryModuleType.REGIONAL_TRENDS,
            title="Emerging Trend Trajectories",
            description="Real-time runway to street adoption signals.",
            items=trend_items,
            action=DiscoveryModuleActionContract(label="View Radar", route="/explore/trends"),
            priority=4,
            visibility=True,
            state=DiscoveryState.READY,
        )
    )

    # 5. Brand Showcase Module
    brand_items = [to_visual_content_model(b, FashionContentType.BRAND) for b in SAMPLE_BRANDS]
    modules.append(
        DiscoveryModuleContract(
            id="mod-brand-showcase",
            module_type=DiscoveryModuleType.BRAND_SHOWCASE,
            title="Artisanal Merchants & Ateliers",
            description="Verified designers and heritage shuttle-loom textile houses.",
            items=brand_items,
            action=DiscoveryModuleActionContract(label="All Brands", route="/explore/brands"),
            priority=5,
            visibility=True,
            state=DiscoveryState.READY,
        )
    )

    return modules


# ---------------------------------------------------------------------------
# Template Builders (Sections 8.5 - 8.14, 8.21 - 8.25)
# ---------------------------------------------------------------------------

def get_discovery_home_template() -> DiscoveryHomeTemplateSpecContract:
    """Build D01 Discovery Home template spec (Section 8.5)."""
    return DiscoveryHomeTemplateSpecContract(
        screen_id=DiscoveryScreenId.D01_DISCOVERY_HOME,
        search_placeholder="Search luxury fashion, street looks, brands...",
        hero=get_discovery_hero(),
        explore_chips=[
            {"id": "products", "label": "Products", "route": "/explore/products"},
            {"id": "looks", "label": "Looks", "route": "/explore/looks"},
            {"id": "collections", "label": "Collections", "route": "/explore/collections"},
            {"id": "styles", "label": "Styles", "route": "/explore/styles"},
            {"id": "brands", "label": "Brands", "route": "/explore/brands"},
            {"id": "trends", "label": "Trends", "route": "/explore/trends"},
        ],
        modules=build_discovery_modules(),
    )


def get_explore_template(explore_type: ExploreType) -> ExploreTemplateSpecContract:
    """Build D02 - D08 focused exploration templates (Sections 8.7 - 8.13)."""
    type_map: dict[ExploreType, tuple[str, str, list[VisualContentModel]]] = {
        ExploreType.FASHION: (
            "Explore Contemporary Fashion",
            "Editorial narratives, styled ensembles, and artisanal collections.",
            [to_visual_content_model(s, FashionContentType.STORY) for s in SAMPLE_STORIES]
            + [to_visual_content_model(l, FashionContentType.LOOK) for l in SAMPLE_LOOKS],
        ),
        ExploreType.PRODUCTS: (
            "Explore Luxury Catalog",
            "Browse normalized garments from verified merchant collective.",
            [to_visual_content_model(p, FashionContentType.PRODUCT) for p in SAMPLE_PRODUCTS],
        ),
        ExploreType.LOOKS: (
            "Explore Styled Ensembles",
            "Complete fashion looks with shoppable constituent garment pieces.",
            [to_visual_content_model(l, FashionContentType.LOOK) for l in SAMPLE_LOOKS],
        ),
        ExploreType.COLLECTIONS: (
            "Curated Seasonal Collections",
            "Thematic wardrobe capsule edits crafted for changing climates and festivities.",
            [to_visual_content_model(c, FashionContentType.COLLECTION) for c in SAMPLE_COLLECTIONS],
        ),
        ExploreType.BRANDS: (
            "Verified Merchant Directory",
            "Independent artisans, heritage looms, and contemporary luxury labels.",
            [to_visual_content_model(b, FashionContentType.BRAND) for b in SAMPLE_BRANDS],
        ),
        ExploreType.STYLES: (
            "Aesthetic Style Taxonomy",
            "Explore aesthetics across boxy streetwear, relaxed tailoring, and artisanal handloom.",
            [to_visual_content_model(s, FashionContentType.STYLE) for s in SAMPLE_STYLES],
        ),
        ExploreType.TRENDS: (
            "Trend Radar & Momentum Signals",
            "Data-driven trajectory points tracking runway emergence to street proliferation.",
            [to_visual_content_model(t, FashionContentType.TREND) for t in SAMPLE_TRENDS],
        ),
    }

    title, description, items = type_map.get(
        explore_type,
        ("Explore FashXStudio", "Explore curated fashion items.", []),
    )

    screen_id_map: dict[ExploreType, DiscoveryScreenId] = {
        ExploreType.FASHION: DiscoveryScreenId.D02_EXPLORE_FASHION,
        ExploreType.PRODUCTS: DiscoveryScreenId.D03_EXPLORE_PRODUCTS,
        ExploreType.LOOKS: DiscoveryScreenId.D04_EXPLORE_LOOKS,
        ExploreType.COLLECTIONS: DiscoveryScreenId.D05_EXPLORE_COLLECTIONS,
        ExploreType.BRANDS: DiscoveryScreenId.D06_EXPLORE_BRANDS,
        ExploreType.STYLES: DiscoveryScreenId.D07_EXPLORE_STYLES,
        ExploreType.TRENDS: DiscoveryScreenId.D08_EXPLORE_TRENDS,
    }

    return ExploreTemplateSpecContract(
        screen_id=screen_id_map.get(explore_type, DiscoveryScreenId.D02_EXPLORE_FASHION),
        explore_type=explore_type,
        title=title,
        description=description,
        featured_items=items[:2],
        grid_items=items,
        total_count=len(items),
    )


def get_personalized_discovery_template(user_id: str = "user-1") -> PersonalizedDiscoveryTemplateSpecContract:
    """Build D09 Personalized Discovery template spec (Section 8.31)."""
    return PersonalizedDiscoveryTemplateSpecContract(
        screen_id=DiscoveryScreenId.D09_PERSONALIZED_DISCOVERY,
        user_id=user_id,
        user_style_tags=["Contemporary Streetwear", "Relaxed Boxy Fit", "Natural Flax Linen", "Japanese Selvedge"],
        modules=build_discovery_modules()[:3],
        recommendation_explanations={
            "prod-denim-01": "Recommended because you explored Japanese selvedge denim in Monsoon capsule.",
            "prod-linen-02": "Matches your saved preferences for breathable summer natural fabrics.",
        },
    )


def get_search_home_template() -> SearchHomeTemplateSpecContract:
    """Build S01 Search Home gateway template spec (Section 8.16)."""
    return SearchHomeTemplateSpecContract(
        screen_id=DiscoveryScreenId.S01_SEARCH_HOME,
        recent_searches=SAMPLE_RECENT_SEARCHES,
        trending_searches=TRENDING_SEARCH_KEYWORDS,
        explore_categories=[
            {"id": "outerwear", "label": "Outerwear & Jackets", "query": "outerwear"},
            {"id": "shirts", "label": "Linen & Casual Shirts", "query": "shirt"},
            {"id": "denim", "label": "Selvedge Denim", "query": "denim"},
            {"id": "streetwear", "label": "Streetwear Looks", "query": "streetwear"},
        ],
    )


def get_search_suggestions(query: str) -> list[SearchSuggestionContract]:
    """Retrieve debounced autocomplete suggestions matching query (Section 8.18 & 8.19)."""
    if not query.strip():
        return SAMPLE_SUGGESTIONS_CATALOG[:4]
    q_clean = query.lower().strip()
    return [s for s in SAMPLE_SUGGESTIONS_CATALOG if q_clean in s.text.lower()]


def search_unified_catalog(
    query: str = "",
    result_type: SearchResultType = SearchResultType.ALL,
    sort: SortOption = SortOption.RELEVANCE,
) -> UnifiedSearchResultsTemplateSpecContract:
    """Execute multi-content search across Products, Looks, Brands, Styles, and Trends (Section 8.21 & 8.22)."""
    q_clean = query.lower().strip()

    # Collect all available models
    all_products = [to_visual_content_model(p, FashionContentType.PRODUCT) for p in SAMPLE_PRODUCTS]
    all_looks = [to_visual_content_model(l, FashionContentType.LOOK) for l in SAMPLE_LOOKS]
    all_brands = [to_visual_content_model(b, FashionContentType.BRAND) for b in SAMPLE_BRANDS]
    all_styles = [to_visual_content_model(s, FashionContentType.STYLE) for s in SAMPLE_STYLES]
    all_trends = [to_visual_content_model(t, FashionContentType.TREND) for t in SAMPLE_TRENDS]

    # Filter by query if supplied
    def matches_query(item: VisualContentModel) -> bool:
        if not q_clean:
            return True
        return (
            q_clean in item.title.lower()
            or (item.subtitle and q_clean in item.subtitle.lower())
            or q_clean in item.category_label.lower()
            or any(q_clean in lbl.lower() for lbl in item.labels)
        )

    matched_products = [i for i in all_products if matches_query(i)]
    matched_looks = [i for i in all_looks if matches_query(i)]
    matched_brands = [i for i in all_brands if matches_query(i)]
    matched_styles = [i for i in all_styles if matches_query(i)]
    matched_trends = [i for i in all_trends if matches_query(i)]

    counts = SearchResultCountsContract(
        all=len(matched_products) + len(matched_looks) + len(matched_brands) + len(matched_styles) + len(matched_trends),
        products=len(matched_products),
        looks=len(matched_looks),
        brands=len(matched_brands),
        styles=len(matched_styles),
        trends=len(matched_trends),
    )

    if result_type == SearchResultType.PRODUCTS:
        selected_items = matched_products
    elif result_type == SearchResultType.LOOKS:
        selected_items = matched_looks
    elif result_type == SearchResultType.BRANDS:
        selected_items = matched_brands
    elif result_type == SearchResultType.STYLES:
        selected_items = matched_styles
    elif result_type == SearchResultType.TRENDS:
        selected_items = matched_trends
    else:
        selected_items = matched_products + matched_looks + matched_brands + matched_styles + matched_trends

    is_empty = len(selected_items) == 0

    screen_id_map: dict[SearchResultType, DiscoveryScreenId] = {
        SearchResultType.ALL: DiscoveryScreenId.S03_PRODUCT_SEARCH_RESULTS,
        SearchResultType.PRODUCTS: DiscoveryScreenId.S03_PRODUCT_SEARCH_RESULTS,
        SearchResultType.LOOKS: DiscoveryScreenId.S04_FASHION_SEARCH_RESULTS,
        SearchResultType.BRANDS: DiscoveryScreenId.S05_BRAND_SEARCH_RESULTS,
        SearchResultType.STYLES: DiscoveryScreenId.S06_STYLE_SEARCH_RESULTS,
        SearchResultType.TRENDS: DiscoveryScreenId.S07_TREND_SEARCH_RESULTS,
    }

    if is_empty:
        screen_id = DiscoveryScreenId.S10_SEARCH_EMPTY_STATE
    else:
        screen_id = screen_id_map.get(result_type, DiscoveryScreenId.S03_PRODUCT_SEARCH_RESULTS)

    return UnifiedSearchResultsTemplateSpecContract(
        screen_id=screen_id,
        query=query,
        active_tab=result_type,
        counts=counts,
        items=selected_items,
        filter_state=FilterStateContract(available_groups=SAMPLE_FILTER_GROUPS, active_filters=[]),
        sort=sort,
        is_empty=is_empty,
        empty_suggestions=["Try 'denim'", "Try 'linen'", "Try 'streetwear'"] if is_empty else [],
    )


def execute_advanced_search(criteria: AdvancedSearchCriteriaContract) -> AdvancedSearchTemplateSpecContract:
    """Execute structured multi-attribute query criteria (Section 8.25)."""
    all_products = [to_visual_content_model(p, FashionContentType.PRODUCT) for p in SAMPLE_PRODUCTS]

    matched: list[VisualContentModel] = []
    for item in all_products:
        if criteria.keywords and criteria.keywords.lower() not in item.title.lower():
            continue
        if criteria.brand and criteria.brand.lower() not in (item.subtitle or "").lower():
            continue
        if criteria.category and criteria.category.lower() not in item.category_label.lower():
            continue
        if criteria.price_min is not None and item.price and item.price.amount < criteria.price_min:
            continue
        if criteria.price_max is not None and item.price and item.price.amount > criteria.price_max:
            continue
        matched.append(item)

    return AdvancedSearchTemplateSpecContract(
        screen_id=DiscoveryScreenId.S09_ADVANCED_SEARCH,
        criteria=criteria,
        preview_results=matched,
        preview_total=len(matched),
    )
