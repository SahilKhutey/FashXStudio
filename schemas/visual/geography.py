"""FashXStudio Regional Maps & Geography UI System Contracts — Phase 11.

Defines Pydantic v2 data contracts for Geographic Hierarchy, Interactive Fashion Maps,
Region View Models, Markers, Clustering, Layers, Local Products, Regional Trends,
Collections, and Cross-System Discovery Loops (Sections 11.1 - 11.105):
- Screen Inventory: M01-M10 Regional & Map Screens
- Geographic Hierarchy: World -> Continent -> Country -> State -> City -> Local Area
- Region Entities: Structured attributes, bounds, coordinates, and content counters
- Map Architecture: Viewport, Markers, Clusters, Layer Controls, and Selection Panels
- Content Bridges: Regional Trends, Local Products, Curated Looks, and Collections
- Accessibility: Non-map alternative navigation and screen-reader semantics

All schemas enforce extra="forbid" via BaseContractModel (Constitution Rule I02).
"""

from enum import StrEnum
from typing import Any
from pydantic import Field
from schemas.base import BaseContractModel
from schemas.visual.fashion import VisualContentModel


# ---------------------------------------------------------------------------
# Enums (Sections 11.2, 11.3, 11.15, 11.48)
# ---------------------------------------------------------------------------

class RegionalScreenId(StrEnum):
    """Screen identifiers for Regional Maps & Geography ecosystem (Section 11.2)."""
    M01_REGIONAL_HOME = "M01"
    M02_FASHION_MAP = "M02"
    M03_REGIONAL_EXPLORER = "M03"
    M04_COUNTRY_VIEW = "M04"
    M05_STATE_VIEW = "M05"
    M06_CITY_VIEW = "M06"
    M07_REGIONAL_TRENDS = "M07"
    M08_LOCAL_PRODUCTS = "M08"
    M09_REGIONAL_COLLECTIONS = "M09"
    M10_LOCATION_DETAIL = "M10"


class RegionType(StrEnum):
    """Authoritative geographic entity classification levels (Section 11.3, 11.4)."""
    CONTINENT = "continent"
    COUNTRY = "country"
    STATE = "state"
    CITY = "city"
    LOCAL_AREA = "local_area"


class MarkerCategory(StrEnum):
    """Semantic category classification for map markers (Section 11.15)."""
    REGION = "region"
    EVENT = "event"
    TREND = "trend"
    STORE = "store"
    COLLECTION = "collection"
    FEATURED_LOCATION = "featured_location"


class GeographyLayerType(StrEnum):
    """Toggleable thematic map layers (Section 11.48, 11.49)."""
    REGIONS = "regions"
    TRENDS = "trends"
    COLLECTIONS = "collections"
    PRODUCTS = "products"


class GeographyState(StrEnum):
    """Operational lifecycle state for regional components (Section 11.58 - 11.62)."""
    READY = "ready"
    LOADING = "loading"
    PARTIAL = "partial"
    EMPTY = "empty"
    ERROR = "error"
    UNAVAILABLE = "unavailable"


# ---------------------------------------------------------------------------
# Core Geography & Hierarchy Models (Sections 11.4, 11.5, 11.19)
# ---------------------------------------------------------------------------

class RegionBreadcrumbContract(BaseContractModel):
    """Breadcrumb node representing geographic hierarchy trail (Section 11.19)."""
    id: str
    name: str
    type: RegionType
    is_current: bool = Field(default=False)


class RegionContract(BaseContractModel):
    """Canonical geographic region entity model (Section 11.4)."""
    id: str
    name: str
    type: RegionType
    parent_id: str | None = Field(default=None)
    country_code: str | None = Field(default=None)
    state_code: str | None = Field(default=None)
    city_code: str | None = Field(default=None)
    latitude: float | None = Field(default=None, ge=-90.0, le=90.0)
    longitude: float | None = Field(default=None, ge=-180.0, le=180.0)
    bounding_box: list[float] | None = Field(default=None, max_length=4, min_length=4)
    timezone: str | None = Field(default=None)
    hero_image_uri: str | None = Field(default=None)
    description: str | None = Field(default=None)
    trends_count: int = Field(default=0, ge=0)
    looks_count: int = Field(default=0, ge=0)
    products_count: int = Field(default=0, ge=0)
    collections_count: int = Field(default=0, ge=0)
    is_supported: bool = Field(default=True)


# ---------------------------------------------------------------------------
# Map Viewport, Markers & Clustering Models (Sections 11.8 - 11.18, 11.69)
# ---------------------------------------------------------------------------

class MapMarkerContract(BaseContractModel):
    """Individual pin located on the interactive map surface (Section 11.15, 11.16)."""
    id: str
    region_id: str
    title: str
    category: MarkerCategory = Field(default=MarkerCategory.REGION)
    latitude: float = Field(ge=-90.0, le=90.0)
    longitude: float = Field(ge=-180.0, le=180.0)
    is_selected: bool = Field(default=False)
    accent_color: str | None = Field(default=None)
    item_count: int = Field(default=1, ge=0)


class MapClusterContract(BaseContractModel):
    """Aggregate cluster grouping proximate markers (Section 11.17)."""
    cluster_id: str
    count: int = Field(ge=2)
    latitude: float = Field(ge=-90.0, le=90.0)
    longitude: float = Field(ge=-180.0, le=180.0)
    region_ids: list[str] = Field(default_factory=list)


class MapViewportContract(BaseContractModel):
    """Camera orientation and bounds of the map canvas (Section 11.9, 11.18)."""
    center_latitude: float = Field(default=20.5937, ge=-90.0, le=90.0)
    center_longitude: float = Field(default=78.9629, ge=-180.0, le=180.0)
    zoom_level: float = Field(default=4.0, ge=1.0, le=20.0)
    bounding_box: list[float] | None = Field(default=None)


class MapViewModelContract(BaseContractModel):
    """Complete map view model consumed by map rendering adapters (Section 11.69)."""
    viewport: MapViewportContract
    markers: list[MapMarkerContract] = Field(default_factory=list)
    clusters: list[MapClusterContract] = Field(default_factory=list)
    active_layers: list[GeographyLayerType] = Field(default_factory=list)
    selected_region_id: str | None = Field(default=None)
    state: GeographyState = Field(default=GeographyState.READY)


# ---------------------------------------------------------------------------
# Regional Content, Trends & Comparison Models (Sections 11.28, 11.34, 11.46)
# ---------------------------------------------------------------------------

class RegionalTrendContract(BaseContractModel):
    """Localized fashion trend tied to geographic context (Section 11.28, 11.29)."""
    id: str
    region_id: str
    region_name: str
    title: str
    context_narrative: str
    momentum: str = Field(default="rising")
    media_uri: str
    related_product_ids: list[str] = Field(default_factory=list)
    related_look_ids: list[str] = Field(default_factory=list)


class RegionalComparisonMetricContract(BaseContractModel):
    """Attribute comparison row across multiple regions (Section 11.46)."""
    name: str
    values_by_region: dict[str, str] = Field(default_factory=dict)


class RegionalComparisonContract(BaseContractModel):
    """Factual side-by-side geographic fashion comparison matrix (Section 11.46)."""
    region_ids: list[str] = Field(default_factory=list)
    regions: list[RegionContract] = Field(default_factory=list)
    metrics: list[RegionalComparisonMetricContract] = Field(default_factory=list)


class RegionalContentCardContract(BaseContractModel):
    """Unified regional feed content card (Section 11.34)."""
    id: str
    content_type: str
    title: str
    subtitle: str | None = Field(default=None)
    media_uri: str
    region_name: str
    region_id: str


# ---------------------------------------------------------------------------
# Screen Templates (M01 – M10, Sections 11.2, 11.6 - 11.24)
# ---------------------------------------------------------------------------

class RegionalHomeTemplateSpecContract(BaseContractModel):
    """M01: Regional Home gateway template specification (Section 11.6, 11.7)."""
    screen_id: RegionalScreenId = Field(default=RegionalScreenId.M01_REGIONAL_HOME)
    featured_region: RegionContract
    popular_regions: list[RegionContract] = Field(default_factory=list)
    featured_map: MapViewModelContract
    regional_trends: list[RegionalTrendContract] = Field(default_factory=list)
    regional_looks: list[VisualContentModel] = Field(default_factory=list)
    local_products: list[VisualContentModel] = Field(default_factory=list)
    regional_collections: list[VisualContentModel] = Field(default_factory=list)


class FashionMapTemplateSpecContract(BaseContractModel):
    """M02: Primary interactive fashion map interface specification (Section 11.8 - 11.14)."""
    screen_id: RegionalScreenId = Field(default=RegionalScreenId.M02_FASHION_MAP)
    map_view: MapViewModelContract
    selected_region: RegionContract | None = Field(default=None)
    available_layers: list[GeographyLayerType] = Field(default_factory=list)
    supported_regions: list[RegionContract] = Field(default_factory=list)


class RegionalExplorerTemplateSpecContract(BaseContractModel):
    """M03: Hierarchical accessible text/list browsing explorer specification (Section 11.25, 11.26)."""
    screen_id: RegionalScreenId = Field(default=RegionalScreenId.M03_REGIONAL_EXPLORER)
    breadcrumbs: list[RegionBreadcrumbContract] = Field(default_factory=list)
    regions: list[RegionContract] = Field(default_factory=list)
    active_search_query: str = Field(default="")
    parent_region: RegionContract | None = Field(default=None)


class CountryTemplateSpecContract(BaseContractModel):
    """M04: Country level fashion culture canvas specification (Section 11.20, 11.21)."""
    screen_id: RegionalScreenId = Field(default=RegionalScreenId.M04_COUNTRY_VIEW)
    country: RegionContract
    breadcrumbs: list[RegionBreadcrumbContract] = Field(default_factory=list)
    states_or_provinces: list[RegionContract] = Field(default_factory=list)
    regional_trends: list[RegionalTrendContract] = Field(default_factory=list)
    popular_styles: list[VisualContentModel] = Field(default_factory=list)
    local_products: list[VisualContentModel] = Field(default_factory=list)
    curated_looks: list[VisualContentModel] = Field(default_factory=list)


class StateTemplateSpecContract(BaseContractModel):
    """M05: State or province level fashion canvas specification (Section 11.22)."""
    screen_id: RegionalScreenId = Field(default=RegionalScreenId.M05_STATE_VIEW)
    state_region: RegionContract
    country_region: RegionContract
    breadcrumbs: list[RegionBreadcrumbContract] = Field(default_factory=list)
    cities: list[RegionContract] = Field(default_factory=list)
    regional_trends: list[RegionalTrendContract] = Field(default_factory=list)
    local_products: list[VisualContentModel] = Field(default_factory=list)
    curated_looks: list[VisualContentModel] = Field(default_factory=list)


class CityTemplateSpecContract(BaseContractModel):
    """M06: City and urban fashion hub canvas specification (Section 11.23)."""
    screen_id: RegionalScreenId = Field(default=RegionalScreenId.M06_CITY_VIEW)
    city: RegionContract
    breadcrumbs: list[RegionBreadcrumbContract] = Field(default_factory=list)
    local_areas: list[RegionContract] = Field(default_factory=list)
    fashion_trends: list[RegionalTrendContract] = Field(default_factory=list)
    local_products: list[VisualContentModel] = Field(default_factory=list)
    local_looks: list[VisualContentModel] = Field(default_factory=list)
    related_cities: list[RegionContract] = Field(default_factory=list)


class RegionalTrendsTemplateSpecContract(BaseContractModel):
    """M07: Dedicated regional trends feed specification (Section 11.28, 11.29)."""
    screen_id: RegionalScreenId = Field(default=RegionalScreenId.M07_REGIONAL_TRENDS)
    region: RegionContract
    trends: list[RegionalTrendContract] = Field(default_factory=list)


class LocalProductsTemplateSpecContract(BaseContractModel):
    """M08: Localized products listing specification reusing commerce grid (Section 11.30, 11.31)."""
    screen_id: RegionalScreenId = Field(default=RegionalScreenId.M08_LOCAL_PRODUCTS)
    region: RegionContract
    products: list[VisualContentModel] = Field(default_factory=list)
    total_count: int = Field(default=0, ge=0)
    available_filters: list[str] = Field(default_factory=list)


class RegionalCollectionsTemplateSpecContract(BaseContractModel):
    """M09: Regional capsule collections template specification (Section 11.32)."""
    screen_id: RegionalScreenId = Field(default=RegionalScreenId.M09_REGIONAL_COLLECTIONS)
    region: RegionContract
    featured_collection: VisualContentModel
    collections: list[VisualContentModel] = Field(default_factory=list)


class LocationDetailTemplateSpecContract(BaseContractModel):
    """M10: Deep contextual location profile specification (Section 11.24)."""
    screen_id: RegionalScreenId = Field(default=RegionalScreenId.M10_LOCATION_DETAIL)
    location: RegionContract
    breadcrumbs: list[RegionBreadcrumbContract] = Field(default_factory=list)
    map_view: MapViewModelContract
    trends: list[RegionalTrendContract] = Field(default_factory=list)
    products: list[VisualContentModel] = Field(default_factory=list)
    looks: list[VisualContentModel] = Field(default_factory=list)
