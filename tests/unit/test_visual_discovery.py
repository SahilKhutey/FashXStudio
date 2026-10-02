"""Unit tests for Discovery & Search Screens System — Phase 08.

Covers DISC-001 through DISC-010 and SEARCH-001 through SEARCH-015 (Section 8.66):
- Discovery Architecture (DISC-001 - DISC-010)
- Search System & Autocomplete (SEARCH-001 - SEARCH-015)
- Advanced Search & Multi-type Tabs
"""

import pytest
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
    ExploreTemplateSpecContract,
    ExploreType,
    PersonalizedDiscoveryTemplateSpecContract,
    RecentSearchContract,
    SearchResultCountsContract,
    SearchResultsTemplateSpecContract as UnifiedSearchResultsTemplateSpecContract,
    SearchResultType,
    SearchHomeTemplateSpecContract,
    SearchSuggestionContract,
    SuggestionType,
)
from api.app.visual.discovery_service import (
    execute_advanced_search,
    get_discovery_hero,
    get_discovery_home_template,
    get_explore_template,
    get_personalized_discovery_template,
    get_search_home_template,
    get_search_suggestions,
    search_unified_catalog,
)


# ---------------------------------------------------------------------------
# DISC-001 - DISC-010: Discovery Architecture & Exploration
# ---------------------------------------------------------------------------

def test_disc_001_discovery_home_template() -> None:
    """DISC-001: Discovery Home renders hero, explore chips, and feed modules."""
    tpl = get_discovery_home_template()
    assert tpl.screen_id == DiscoveryScreenId.D01_DISCOVERY_HOME
    assert tpl.hero is not None
    assert len(tpl.explore_chips) == 6
    assert len(tpl.modules) >= 4


def test_disc_002_hero_renders_with_actions() -> None:
    """DISC-002: Hero visual banner exposes primary and secondary action routes."""
    hero = get_discovery_hero()
    assert hero.id == "hero-monsoon-26"
    assert "Monsoon" in hero.title
    assert hero.primary_action_label == "Explore Collection"
    assert hero.primary_action_route.startswith("/explore/")
    assert hero.secondary_action_label is not None


def test_disc_003_modules_structure_and_types() -> None:
    """DISC-003: Discovery modules define archetypes, priority, and visual items."""
    tpl = get_discovery_home_template()
    module_types = {m.module_type for m in tpl.modules}
    assert DiscoveryModuleType.EDITORIAL_STORY in module_types
    assert DiscoveryModuleType.TRENDING_PRODUCTS in module_types
    assert DiscoveryModuleType.RECOMMENDED_LOOKS in module_types
    assert DiscoveryModuleType.REGIONAL_TRENDS in module_types
    assert DiscoveryModuleType.BRAND_SHOWCASE in module_types


def test_disc_004_rail_module_item_count() -> None:
    """DISC-004: Trending products rail module contains valid VisualContentModel items."""
    tpl = get_discovery_home_template()
    mod = next(m for m in tpl.modules if m.module_type == DiscoveryModuleType.TRENDING_PRODUCTS)
    assert len(mod.items) >= 2
    assert mod.items[0].content_type == "product"
    assert mod.action is not None
    assert mod.action.label == "View All"


def test_disc_005_explore_fashion_mixed_content() -> None:
    """DISC-005: D02 Explore Fashion aggregates stories and looks."""
    explore = get_explore_template(ExploreType.FASHION)
    assert explore.screen_id == DiscoveryScreenId.D02_EXPLORE_FASHION
    assert explore.explore_type == ExploreType.FASHION
    assert len(explore.grid_items) >= 2
    content_types = {item.content_type for item in explore.grid_items}
    assert "story" in content_types or "look" in content_types


def test_disc_006_explore_template_taxonomy() -> None:
    """DISC-006: Explore templates cover products, looks, collections, brands, styles, trends."""
    for exp_type, expected_screen in [
        (ExploreType.PRODUCTS, DiscoveryScreenId.D03_EXPLORE_PRODUCTS),
        (ExploreType.LOOKS, DiscoveryScreenId.D04_EXPLORE_LOOKS),
        (ExploreType.COLLECTIONS, DiscoveryScreenId.D05_EXPLORE_COLLECTIONS),
        (ExploreType.BRANDS, DiscoveryScreenId.D06_EXPLORE_BRANDS),
        (ExploreType.STYLES, DiscoveryScreenId.D07_EXPLORE_STYLES),
        (ExploreType.TRENDS, DiscoveryScreenId.D08_EXPLORE_TRENDS),
    ]:
        tpl = get_explore_template(exp_type)
        assert tpl.screen_id == expected_screen
        assert len(tpl.grid_items) >= 1


def test_disc_009_personalized_discovery_explanations() -> None:
    """DISC-009: D09 Personalized discovery provides style tags and recommendation reasons."""
    pers = get_personalized_discovery_template("user-test-42")
    assert pers.screen_id == DiscoveryScreenId.D09_PERSONALIZED_DISCOVERY
    assert pers.user_id == "user-test-42"
    assert len(pers.user_style_tags) >= 2
    assert "Contemporary Streetwear" in pers.user_style_tags
    assert len(pers.recommendation_explanations) >= 1
    assert "selvedge denim" in pers.recommendation_explanations["prod-denim-01"]


def test_disc_010_extra_fields_forbidden() -> None:
    """DISC-010: Discovery contracts strictly reject unauthorized fields via extra='forbid'."""
    with pytest.raises(Exception):
        DiscoveryHeroContract(
            id="hero-fail",
            title="Fail",
            subtitle="Fail",
            media_uri="https://images.fashx.com/fail.jpg",
            primary_action_label="Fail",
            primary_action_route="/fail",
            unauthorized_css="red",  # type: ignore
        )


# ---------------------------------------------------------------------------
# SEARCH-001 - SEARCH-015: Search Engine, Autocomplete & Tabs
# ---------------------------------------------------------------------------

def test_search_001_search_home_gateway() -> None:
    """SEARCH-001: S01 Search Home exposes recent queries and trending tags."""
    home = get_search_home_template()
    assert home.screen_id == DiscoveryScreenId.S01_SEARCH_HOME
    assert len(home.recent_searches) >= 3
    assert len(home.trending_searches) >= 4
    assert "Raw Denim" in home.trending_searches
    assert len(home.explore_categories) >= 3


def test_search_002_suggestions_autocomplete() -> None:
    """SEARCH-002: Autocomplete suggestions return matching queries with types."""
    suggestions = get_search_suggestions("lin")
    assert len(suggestions) >= 2
    s_texts = [s.text for s in suggestions]
    assert "linen shirts" in s_texts
    assert "linen camp collar shirt" in s_texts


def test_search_003_suggestion_categorization() -> None:
    """SEARCH-003: Autocomplete suggestions preserve SuggestionType (brand, product, style)."""
    brand_sug = get_search_suggestions("RawDenim")
    assert len(brand_sug) >= 1
    assert brand_sug[0].suggestion_type == SuggestionType.BRAND
    assert brand_sug[0].target_id == "brand-raw-denim"


def test_search_005_unified_search_all() -> None:
    """SEARCH-005: Unified search aggregates products, looks, brands, styles, and trends."""
    res = search_unified_catalog(query="")
    assert res.counts.all >= 5
    assert res.counts.products >= 2
    assert res.counts.looks >= 1
    assert res.counts.brands >= 1
    assert res.counts.styles >= 1
    assert res.counts.trends >= 1
    assert len(res.items) == res.counts.all


def test_search_006_search_by_query_filter() -> None:
    """SEARCH-006: Searching for specific keyword filters items correctly."""
    res = search_unified_catalog(query="denim")
    assert res.counts.all >= 1
    for item in res.items:
        matches = (
            "denim" in item.title.lower()
            or (item.subtitle and "denim" in item.subtitle.lower())
            or any("denim" in l.lower() for l in item.labels)
        )
        assert matches


def test_search_007_search_tab_filtering() -> None:
    """SEARCH-007: Selecting result_type tab isolates items of that content dimension."""
    res_looks = search_unified_catalog(query="", result_type=SearchResultType.LOOKS)
    assert res_looks.active_tab == SearchResultType.LOOKS
    assert len(res_looks.items) == res_looks.counts.looks
    assert all(i.content_type == "look" for i in res_looks.items)

    res_brands = search_unified_catalog(query="", result_type=SearchResultType.BRANDS)
    assert res_brands.active_tab == SearchResultType.BRANDS
    assert len(res_brands.items) == res_brands.counts.brands
    assert all(i.content_type == "brand" for i in res_brands.items)


def test_search_008_search_empty_state() -> None:
    """SEARCH-008: Search query with zero matches returns S10 empty state and suggestions."""
    res_empty = search_unified_catalog(query="nonexistent_xyz_123")
    assert res_empty.is_empty is True
    assert len(res_empty.items) == 0
    assert len(res_empty.empty_suggestions) >= 1
    assert any("denim" in s.lower() for s in res_empty.empty_suggestions)


def test_search_010_advanced_search_criteria() -> None:
    """SEARCH-010: S09 Advanced Search matches structured criteria (keywords, brand, price)."""
    criteria = AdvancedSearchCriteriaContract(
        keywords="jacket",
        brand="RawDenim",
        price_max=6000.0,
    )
    adv = execute_advanced_search(criteria)
    assert adv.screen_id == DiscoveryScreenId.S09_ADVANCED_SEARCH
    assert adv.preview_total >= 1
    assert adv.preview_results[0].title == "Selvedge Oversized Denim Jacket"
