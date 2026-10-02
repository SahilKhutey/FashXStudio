"""FashXStudio Discovery & Search Screens System Contracts — Phase 08.

Defines Pydantic v2 data contracts for Discovery + Search + Exploration (Sections 8.1-8.82):
- Discovery Architecture: DiscoveryHero, DiscoveryModule, DiscoveryViewModel, DiscoveryRail, DiscoveryGrid
- Screen Inventory: D01-D10 Discovery Screens, S01-S10 Search Screens
- Search Engine: Query state, debounced suggestions, recent searches, multi-type navigation (All, Products, Looks, Brands, Styles, Trends)
- Advanced Search: Structured multi-criteria query and preview
- Personalization & Recommendations: Explainable modules with user style tags
- Templates: DiscoveryHomeTemplate, ExploreTemplate, SearchHomeTemplate, AdvancedSearchTemplate, DiscoveryResultsTemplate

All schemas enforce extra="forbid" via BaseContractModel (Constitution Rule I02).
"""

from enum import StrEnum
from typing import Any
from pydantic import Field
from schemas.base import BaseContractModel
from schemas.visual.fashion import VisualContentModel
from schemas.visual.shopping import FilterStateContract, SortOption


# ---------------------------------------------------------------------------
# Enums (Sections 8.3, 8.18, 8.22, 8.35, 8.50)
# ---------------------------------------------------------------------------

class DiscoveryScreenId(StrEnum):
    """Screen identifiers for Discovery & Search ecosystem (Section 8.3)."""
    # Discovery Screens (D01 - D10)
    D01_DISCOVERY_HOME = "D01"
    D02_EXPLORE_FASHION = "D02"
    D03_EXPLORE_PRODUCTS = "D03"
    D04_EXPLORE_LOOKS = "D04"
    D05_EXPLORE_COLLECTIONS = "D05"
    D06_EXPLORE_BRANDS = "D06"
    D07_EXPLORE_STYLES = "D07"
    D08_EXPLORE_TRENDS = "D08"
    D09_PERSONALIZED_DISCOVERY = "D09"
    D10_DISCOVERY_RESULTS = "D10"

    # Search Screens (S01 - S10)
    S01_SEARCH_HOME = "S01"
    S02_SEARCH_SUGGESTIONS = "S02"
    S03_PRODUCT_SEARCH_RESULTS = "S03"
    S04_FASHION_SEARCH_RESULTS = "S04"
    S05_BRAND_SEARCH_RESULTS = "S05"
    S06_STYLE_SEARCH_RESULTS = "S06"
    S07_TREND_SEARCH_RESULTS = "S07"
    S08_SEARCH_FILTERS = "S08"
    S09_ADVANCED_SEARCH = "S09"
    S10_SEARCH_EMPTY_STATE = "S10"


class ExploreType(StrEnum):
    """Exploration taxonomy domain types (Section 8.7 - 8.13)."""
    FASHION = "fashion"
    PRODUCTS = "products"
    LOOKS = "looks"
    COLLECTIONS = "collections"
    BRANDS = "brands"
    STYLES = "styles"
    TRENDS = "trends"


class SearchResultType(StrEnum):
    """Result-type tab navigation dimensions (Section 8.22)."""
    ALL = "all"
    PRODUCTS = "products"
    LOOKS = "looks"
    BRANDS = "brands"
    STYLES = "styles"
    TRENDS = "trends"


class SuggestionType(StrEnum):
    """Categorized search autocomplete suggestions (Section 8.18)."""
    QUERY = "query"
    PRODUCT = "product"
    BRAND = "brand"
    STYLE = "style"
    TREND = "trend"
    CATEGORY = "category"


class DiscoveryModuleType(StrEnum):
    """Module archetypes for discovery feed composition (Section 8.35)."""
    FEATURED_COLLECTION = "featured_collection"
    TRENDING_PRODUCTS = "trending_products"
    POPULAR_STYLES = "popular_styles"
    RECOMMENDED_LOOKS = "recommended_looks"
    REGIONAL_TRENDS = "regional_trends"
    EDITORIAL_STORY = "editorial_story"
    BRAND_SHOWCASE = "brand_showcase"


class DiscoveryState(StrEnum):
    """Module and surface loading/error state (Section 8.50)."""
    LOADING = "loading"
    READY = "ready"
    EMPTY = "empty"
    PARTIAL = "partial"
    ERROR = "error"
    UNAVAILABLE = "unavailable"


# ---------------------------------------------------------------------------
# Discovery Architecture & Modules (Sections 8.5 - 8.14, 8.34 - 8.38)
# ---------------------------------------------------------------------------

class DiscoveryHeroContract(BaseContractModel):
    """Visual gateway hero banner with actions (Section 8.6)."""
    id: str
    title: str
    subtitle: str
    media_uri: str
    primary_action_label: str
    primary_action_route: str
    secondary_action_label: str | None = Field(default=None)
    secondary_action_route: str | None = Field(default=None)


class DiscoveryModuleActionContract(BaseContractModel):
    """Action trigger for discovery modules (Section 8.35)."""
    label: str
    route: str


class DiscoveryModuleContract(BaseContractModel):
    """Self-contained modular discovery unit (Section 8.35)."""
    id: str
    module_type: DiscoveryModuleType
    title: str
    description: str | None = Field(default=None)
    items: list[VisualContentModel] = Field(default_factory=list)
    action: DiscoveryModuleActionContract | None = Field(default=None)
    priority: int = Field(default=0)
    visibility: bool = Field(default=True)
    state: DiscoveryState = Field(default=DiscoveryState.READY)


class DiscoveryViewModelContract(BaseContractModel):
    """Unified discovery screen view model (Section 8.63)."""
    hero: DiscoveryHeroContract | None = Field(default=None)
    modules: list[DiscoveryModuleContract] = Field(default_factory=list)
    has_personalization: bool = Field(default=False)
    state: DiscoveryState = Field(default=DiscoveryState.READY)


# ---------------------------------------------------------------------------
# Search System & Autocomplete Models (Sections 8.15 - 8.25, 8.64)
# ---------------------------------------------------------------------------

class SearchSuggestionContract(BaseContractModel):
    """Categorized suggestion item for autocomplete (Section 8.18)."""
    text: str
    suggestion_type: SuggestionType
    target_id: str | None = Field(default=None)
    count: int | None = Field(default=None, ge=0)
    category: str | None = Field(default=None)


class RecentSearchContract(BaseContractModel):
    """User search history entry (Section 8.20)."""
    query: str
    timestamp: str


class SearchResultCountsContract(BaseContractModel):
    """Tab-level result counts across content types (Section 8.22)."""
    all: int = Field(default=0, ge=0)
    products: int = Field(default=0, ge=0)
    looks: int = Field(default=0, ge=0)
    brands: int = Field(default=0, ge=0)
    styles: int = Field(default=0, ge=0)
    trends: int = Field(default=0, ge=0)


class AdvancedSearchCriteriaContract(BaseContractModel):
    """Structured multi-attribute query criteria (Section 8.25)."""
    keywords: str | None = Field(default=None)
    category: str | None = Field(default=None)
    brand: str | None = Field(default=None)
    style: str | None = Field(default=None)
    price_min: float | None = Field(default=None, ge=0.0)
    price_max: float | None = Field(default=None, ge=0.0)
    color: str | None = Field(default=None)
    size: str | None = Field(default=None)
    region: str | None = Field(default=None)


class SearchViewModelContract(BaseContractModel):
    """Unified search screen view model (Section 8.64)."""
    query: str
    result_type: SearchResultType = Field(default=SearchResultType.ALL)
    counts: SearchResultCountsContract
    results: list[VisualContentModel] = Field(default_factory=list)
    suggestions: list[SearchSuggestionContract] = Field(default_factory=list)
    recent_searches: list[RecentSearchContract] = Field(default_factory=list)
    filter_state: FilterStateContract | None = Field(default=None)
    sort: SortOption = Field(default=SortOption.RELEVANCE)
    state: DiscoveryState = Field(default=DiscoveryState.READY)


# ---------------------------------------------------------------------------
# Templates (D01 - D10, S01 - S10, Section 8.61)
# ---------------------------------------------------------------------------

class DiscoveryHomeTemplateSpecContract(BaseContractModel):
    """D01: Primary Discovery Home template spec (Section 8.5)."""
    screen_id: DiscoveryScreenId = Field(default=DiscoveryScreenId.D01_DISCOVERY_HOME)
    search_placeholder: str = Field(default="Search fashion, products, styles, trends...")
    hero: DiscoveryHeroContract
    explore_chips: list[dict[str, str]] = Field(default_factory=list)
    modules: list[DiscoveryModuleContract] = Field(default_factory=list)


class ExploreTemplateSpecContract(BaseContractModel):
    """D02 - D08: Focused exploration template spec (Sections 8.7 - 8.13)."""
    screen_id: DiscoveryScreenId
    explore_type: ExploreType
    title: str
    description: str
    featured_items: list[VisualContentModel] = Field(default_factory=list)
    grid_items: list[VisualContentModel] = Field(default_factory=list)
    total_count: int = Field(default=0, ge=0)


class PersonalizedDiscoveryTemplateSpecContract(BaseContractModel):
    """D09: Personalized discovery experience template spec (Section 8.31)."""
    screen_id: DiscoveryScreenId = Field(default=DiscoveryScreenId.D09_PERSONALIZED_DISCOVERY)
    user_id: str
    user_style_tags: list[str] = Field(default_factory=list)
    modules: list[DiscoveryModuleContract] = Field(default_factory=list)
    recommendation_explanations: dict[str, str] = Field(default_factory=dict)


class DiscoveryResultsTemplateSpecContract(BaseContractModel):
    """D10: Multi-type mixed discovery results template spec (Section 8.14)."""
    screen_id: DiscoveryScreenId = Field(default=DiscoveryScreenId.D10_DISCOVERY_RESULTS)
    query: str
    results_by_type: dict[str, list[VisualContentModel]] = Field(default_factory=dict)
    total_count: int = Field(default=0, ge=0)


class SearchHomeTemplateSpecContract(BaseContractModel):
    """S01: Search home gateway template spec (Section 8.16)."""
    screen_id: DiscoveryScreenId = Field(default=DiscoveryScreenId.S01_SEARCH_HOME)
    recent_searches: list[RecentSearchContract] = Field(default_factory=list)
    trending_searches: list[str] = Field(default_factory=list)
    explore_categories: list[dict[str, str]] = Field(default_factory=list)


class SearchResultsTemplateSpecContract(BaseContractModel):
    """S03 - S07, S10: Search results template spec (Section 8.21)."""
    screen_id: DiscoveryScreenId = Field(default=DiscoveryScreenId.S03_PRODUCT_SEARCH_RESULTS)
    query: str
    active_tab: SearchResultType = Field(default=SearchResultType.ALL)
    counts: SearchResultCountsContract
    items: list[VisualContentModel] = Field(default_factory=list)
    filter_state: FilterStateContract | None = Field(default=None)
    sort: SortOption = Field(default=SortOption.RELEVANCE)
    is_empty: bool = Field(default=False)
    empty_suggestions: list[str] = Field(default_factory=list)


class AdvancedSearchTemplateSpecContract(BaseContractModel):
    """S09: Structured advanced search template spec (Section 8.25)."""
    screen_id: DiscoveryScreenId = Field(default=DiscoveryScreenId.S09_ADVANCED_SEARCH)
    criteria: AdvancedSearchCriteriaContract
    preview_results: list[VisualContentModel] = Field(default_factory=list)
    preview_total: int = Field(default=0, ge=0)
