"""Unit tests for Regional Maps & Geography UI System — Phase 11.

Verifies:
- REGION-001 to REGION-005: Canonical Geographic Hierarchy (World, Country, State, City, Local Area)
- REGION-006 to REGION-010: Authoritative Root-to-Leaf Breadcrumbs Engine
- REGION-011 to REGION-015: Child Resolution & Hierarchy Relational Integrity
- REGION-016 to REGION-020: Regional Search & Side-by-Side Comparison Engine
- REGION-021 to REGION-027: Screen Template Specifications (M01, M03, M04, M05, M06, M07, M08, M09, M10)
- MAP-001 to MAP-010: Map View Models, Viewports, Markers, Density Clusters & Layer Toggles (M02)
- FORBID-001 to FORBID-008: Extra Fields Forbidden across all Geography Contracts (Constitution Rule I02).
"""

import pytest
from pydantic import ValidationError

from schemas.visual.geography import (
    CityTemplateSpecContract,
    CountryTemplateSpecContract,
    FashionMapTemplateSpecContract,
    GeographyLayerType,
    GeographyState,
    LocalProductsTemplateSpecContract,
    LocationDetailTemplateSpecContract,
    MapClusterContract,
    MapMarkerContract,
    MapViewModelContract,
    MapViewportContract,
    MarkerCategory,
    RegionBreadcrumbContract,
    RegionContract,
    RegionType,
    RegionalCollectionsTemplateSpecContract,
    RegionalComparisonContract,
    RegionalComparisonMetricContract,
    RegionalExplorerTemplateSpecContract,
    RegionalHomeTemplateSpecContract,
    RegionalScreenId,
    RegionalTrendContract,
    RegionalTrendsTemplateSpecContract,
    StateTemplateSpecContract,
)
from api.app.visual.geography_service import (
    CANONICAL_REGIONS,
    REGIONAL_TRENDS_FIXTURES,
    REGIONS_REGISTRY,
    build_map_clusters,
    build_map_markers,
    build_map_view_model,
    compare_regions,
    get_child_regions,
    get_city_template,
    get_country_template,
    get_fashion_map_template,
    get_local_products_template,
    get_location_detail_template,
    get_region_breadcrumbs,
    get_regional_collections_template,
    get_regional_explorer_template,
    get_regional_home_template,
    get_regional_trends_template,
    get_state_template,
    reset_geography_fixtures,
    search_regions,
)


@pytest.fixture(autouse=True)
def setup_geography_isolation():
    """Ensure in-memory registry is fresh before and after every test."""
    reset_geography_fixtures()
    yield
    reset_geography_fixtures()


# ===========================================================================
# REGION-001 to REGION-005: Canonical Geographic Hierarchy
# ===========================================================================

def test_region_001_canonical_countries_present():
    """REGION-001: Verifies top-level canonical countries India, Japan, France exist."""
    assert "reg-india" in REGIONS_REGISTRY
    assert "reg-japan" in REGIONS_REGISTRY
    assert "reg-france" in REGIONS_REGISTRY

    india = REGIONS_REGISTRY["reg-india"]
    assert india.type == RegionType.COUNTRY
    assert india.country_code == "IN"
    assert india.parent_id is None


def test_region_002_india_hierarchy_three_tiers():
    """REGION-002: Verifies India -> Chhattisgarh -> Raipur hierarchy chain."""
    ct = REGIONS_REGISTRY["reg-chhattisgarh"]
    assert ct.type == RegionType.STATE
    assert ct.parent_id == "reg-india"

    raipur = REGIONS_REGISTRY["reg-raipur"]
    assert raipur.type == RegionType.CITY
    assert raipur.parent_id == "reg-chhattisgarh"
    assert "Kosa" in (ct.description or "")
    assert "Dhokra" in (raipur.description or "")


def test_region_003_japan_denim_capital_hierarchy():
    """REGION-003: Verifies Japan -> Okayama -> Kojima Denim Street hierarchy."""
    okayama = REGIONS_REGISTRY["reg-okayama"]
    assert okayama.type == RegionType.STATE
    assert okayama.parent_id == "reg-japan"

    kojima = REGIONS_REGISTRY["reg-kojima"]
    assert kojima.type == RegionType.CITY
    assert kojima.parent_id == "reg-okayama"
    assert "selvedge" in (kojima.description or "").lower()


def test_region_004_france_couture_hierarchy():
    """REGION-004: Verifies France -> Paris couture capital hierarchy."""
    paris = REGIONS_REGISTRY["reg-paris"]
    assert paris.type == RegionType.CITY
    assert paris.parent_id == "reg-france"
    assert "Parisian" in (paris.description or "")


def test_region_005_geographic_coordinates_and_bounds():
    """REGION-005: Verifies regions contain valid latitude, longitude, and bounding boxes."""
    raipur = REGIONS_REGISTRY["reg-raipur"]
    assert -90.0 <= raipur.latitude <= 90.0
    assert -180.0 <= raipur.longitude <= 180.0
    assert raipur.bounding_box is not None
    assert len(raipur.bounding_box) == 4
    min_lat, min_lon, max_lat, max_lon = raipur.bounding_box
    assert min_lat < max_lat
    assert min_lon < max_lon


# ===========================================================================
# REGION-006 to REGION-010: Authoritative Breadcrumbs Engine
# ===========================================================================

def test_region_006_leaf_city_breadcrumbs_full_chain():
    """REGION-006: Leaf city breadcrumbs must resolve complete root-to-leaf path."""
    crumbs = get_region_breadcrumbs("reg-raipur")
    assert len(crumbs) == 3
    assert [c.id for c in crumbs] == ["reg-india", "reg-chhattisgarh", "reg-raipur"]
    assert not crumbs[0].is_current
    assert not crumbs[1].is_current
    assert crumbs[2].is_current


def test_region_007_country_root_breadcrumb_single():
    """REGION-007: Root level country has single self-referential breadcrumb."""
    crumbs = get_region_breadcrumbs("reg-india")
    assert len(crumbs) == 1
    assert crumbs[0].id == "reg-india"
    assert crumbs[0].is_current is True


def test_region_008_state_breadcrumbs_two_levels():
    """REGION-008: State level has two breadcrumb items."""
    crumbs = get_region_breadcrumbs("reg-maharashtra")
    assert len(crumbs) == 2
    assert crumbs[0].id == "reg-india"
    assert crumbs[1].id == "reg-maharashtra"
    assert crumbs[1].is_current is True


def test_region_009_nonexistent_region_empty_breadcrumbs():
    """REGION-009: Nonexistent region returns empty breadcrumb list."""
    crumbs = get_region_breadcrumbs("reg-atlantis")
    assert crumbs == []


def test_region_010_breadcrumb_contract_immutability_and_types():
    """REGION-010: Breadcrumbs strictly adhere to RegionBreadcrumbContract."""
    crumb = RegionBreadcrumbContract(
        id="reg-test",
        name="Test",
        type=RegionType.CITY,
        is_current=True,
    )
    assert crumb.type == RegionType.CITY
    assert crumb.is_current is True


# ===========================================================================
# REGION-011 to REGION-015: Child Resolution & Hierarchy Relational Integrity
# ===========================================================================

def test_region_011_get_child_regions_for_country():
    """REGION-011: get_child_regions resolves states under a country."""
    states = get_child_regions("reg-india")
    state_ids = [s.id for s in states]
    assert "reg-chhattisgarh" in state_ids
    assert "reg-maharashtra" in state_ids
    assert "reg-karnataka" in state_ids


def test_region_012_get_child_regions_for_state():
    """REGION-012: get_child_regions resolves cities under a state."""
    cities = get_child_regions("reg-chhattisgarh")
    assert len(cities) >= 1
    assert cities[0].id == "reg-raipur"


def test_region_013_leaf_region_children_empty():
    """REGION-013: Leaf region has no child regions."""
    children = get_child_regions("reg-raipur")
    assert children == []


def test_region_014_parent_relationship_integrity():
    """REGION-014: Every non-root region points to a valid parent in the registry."""
    for reg_id, reg in REGIONS_REGISTRY.items():
        if reg.parent_id is not None:
            assert reg.parent_id in REGIONS_REGISTRY, f"{reg_id} points to missing parent {reg.parent_id}"


def test_region_015_catalog_metrics_positive():
    """REGION-015: Pre-computed catalog metrics are non-negative."""
    for reg in REGIONS_REGISTRY.values():
        assert reg.products_count >= 0
        assert reg.looks_count >= 0
        assert reg.trends_count >= 0
        assert reg.collections_count >= 0


# ===========================================================================
# REGION-016 to REGION-020: Search & Comparison Engine
# ===========================================================================

def test_region_016_search_by_name_substring():
    """REGION-016: search_regions matches query substrings against region names."""
    results = search_regions("Rai")
    assert any(r.id == "reg-raipur" for r in results)


def test_region_017_search_by_description():
    """REGION-017: search_regions matches substrings in region descriptions."""
    results = search_regions("selvedge")
    assert any(r.id == "reg-kojima" for r in results)


def test_region_018_search_filter_by_type():
    """REGION-018: search_regions respects RegionType filter."""
    cities = search_regions("", region_type=RegionType.CITY)
    assert all(c.type == RegionType.CITY for c in cities)
    assert len(cities) >= 4


def test_region_019_compare_two_regions():
    """REGION-019: compare_regions constructs multi-metric comparison matrix."""
    comp = compare_regions(["reg-raipur", "reg-mumbai"])
    assert comp.region_ids == ["reg-raipur", "reg-mumbai"]
    assert len(comp.regions) == 2
    assert len(comp.metrics) >= 3
    # Check textile craft comparison metric
    textile_metric = comp.metrics[0]
    assert textile_metric.name == "Primary Textile Craft"
    assert "reg-raipur" in textile_metric.values_by_region
    assert "Kosa" in textile_metric.values_by_region["reg-raipur"]


def test_region_020_compare_regions_fallback_defaults():
    """REGION-020: compare_regions with empty list falls back to default canonical comparison."""
    comp = compare_regions([])
    assert len(comp.regions) == 2
    assert "reg-raipur" in comp.region_ids


# ===========================================================================
# REGION-021 to REGION-027: Screen Template Specifications (M01, M03–M10)
# ===========================================================================

def test_region_021_m01_regional_home_template():
    """REGION-021: M01 Regional Home template spec contains featured region, map, trends, and feeds."""
    spec = get_regional_home_template()
    assert spec.screen_id == RegionalScreenId.M01_REGIONAL_HOME
    assert spec.featured_region.id == "reg-india"
    assert len(spec.popular_regions) >= 4
    assert spec.featured_map.state == GeographyState.READY
    assert len(spec.regional_trends) >= 1
    assert len(spec.regional_looks) >= 1
    assert len(spec.local_products) >= 1


def test_region_022_m03_regional_explorer_modes():
    """REGION-022: M03 Regional Explorer supports root countries, child exploration, and query search."""
    # Mode 1: Root countries
    spec_root = get_regional_explorer_template()
    assert spec_root.screen_id == RegionalScreenId.M03_REGIONAL_EXPLORER
    assert all(r.type == RegionType.COUNTRY for r in spec_root.regions)

    # Mode 2: Drilldown under India
    spec_drill = get_regional_explorer_template(parent_id="reg-india")
    assert spec_drill.parent_region is not None
    assert spec_drill.parent_region.id == "reg-india"
    assert len(spec_drill.breadcrumbs) == 1
    assert any(r.id == "reg-chhattisgarh" for r in spec_drill.regions)

    # Mode 3: Active search
    spec_search = get_regional_explorer_template(query="Paris")
    assert len(spec_search.regions) == 1
    assert spec_search.regions[0].id == "reg-paris"
    assert spec_search.active_search_query == "Paris"


def test_region_023_m04_country_view_spec():
    """REGION-023: M04 Country View contains states, trends, styles, products, and looks."""
    spec = get_country_template("reg-india")
    assert spec.screen_id == RegionalScreenId.M04_COUNTRY_VIEW
    assert spec.country.id == "reg-india"
    assert len(spec.states_or_provinces) >= 3
    assert len(spec.regional_trends) >= 1
    assert len(spec.popular_styles) >= 1


def test_region_024_m05_state_view_spec():
    """REGION-024: M05 State View contains parent country, cities, and local products."""
    spec = get_state_template("reg-chhattisgarh")
    assert spec.screen_id == RegionalScreenId.M05_STATE_VIEW
    assert spec.state_region.id == "reg-chhattisgarh"
    assert spec.country_region.id == "reg-india"
    assert any(c.id == "reg-raipur" for c in spec.cities)
    assert len(spec.breadcrumbs) == 2


def test_region_025_m06_city_view_spec():
    """REGION-025: M06 City View contains local street movements and related fashion cities."""
    spec = get_city_template("reg-raipur")
    assert spec.screen_id == RegionalScreenId.M06_CITY_VIEW
    assert spec.city.id == "reg-raipur"
    assert len(spec.fashion_trends) >= 1
    assert len(spec.related_cities) >= 1
    assert len(spec.breadcrumbs) == 3


def test_region_026_m07_and_m08_specs():
    """REGION-026: M07 Trends feed and M08 Local Products catalogue specs."""
    trends_spec = get_regional_trends_template("reg-raipur")
    assert trends_spec.screen_id == RegionalScreenId.M07_REGIONAL_TRENDS
    assert trends_spec.region.id == "reg-raipur"
    assert len(trends_spec.trends) >= 1

    prod_spec = get_local_products_template("reg-raipur")
    assert prod_spec.screen_id == RegionalScreenId.M08_LOCAL_PRODUCTS
    assert prod_spec.total_count == len(prod_spec.products)
    assert len(prod_spec.available_filters) >= 3


def test_region_027_m09_and_m10_specs():
    """REGION-027: M09 Regional Collections and M10 Location Detail specs."""
    coll_spec = get_regional_collections_template("reg-raipur")
    assert coll_spec.screen_id == RegionalScreenId.M09_REGIONAL_COLLECTIONS
    assert coll_spec.featured_collection is not None
    assert len(coll_spec.collections) >= 1

    loc_spec = get_location_detail_template("reg-raipur")
    assert loc_spec.screen_id == RegionalScreenId.M10_LOCATION_DETAIL
    assert loc_spec.location.id == "reg-raipur"
    assert loc_spec.map_view.selected_region_id == "reg-raipur"
    assert len(loc_spec.breadcrumbs) == 3


# ===========================================================================
# MAP-001 to MAP-010: Map View Models, Markers, Clusters & Layers (M02)
# ===========================================================================

def test_map_001_view_model_default_viewport():
    """MAP-001: build_map_view_model provides correct initial viewport."""
    vm = build_map_view_model()
    assert vm.viewport.center_latitude == 20.5937
    assert vm.viewport.center_longitude == 78.9629
    assert vm.state == GeographyState.READY
    assert vm.selected_region_id == "reg-india"


def test_map_002_viewport_zoom_level_by_region_type():
    """MAP-002: Viewport zoom level scales appropriately with region hierarchy."""
    vm_country = build_map_view_model("reg-india")
    assert vm_country.viewport.zoom_level == 3.5

    vm_state = build_map_view_model("reg-chhattisgarh")
    assert vm_state.viewport.zoom_level == 4.5

    vm_city = build_map_view_model("reg-raipur")
    assert vm_city.viewport.zoom_level == 6.0


def test_map_003_markers_built_and_categorized():
    """MAP-003: Markers are constructed with valid coordinates and categories."""
    markers = build_map_markers()
    assert len(markers) >= 5
    categories = {m.category for m in markers}
    assert MarkerCategory.REGION in categories
    assert MarkerCategory.FEATURED_LOCATION in categories


def test_map_004_marker_selection_flag():
    """MAP-004: Selected region marks corresponding marker as selected."""
    markers = build_map_markers(selected_region_id="reg-raipur")
    selected_markers = [m for m in markers if m.is_selected]
    assert len(selected_markers) == 1
    assert selected_markers[0].region_id == "reg-raipur"


def test_map_005_density_clusters_structure():
    """MAP-005: Map clusters group regional nodes with aggregate count and coordinates."""
    clusters = build_map_clusters()
    assert len(clusters) >= 2
    india_cluster = next((c for c in clusters if c.cluster_id == "cluster-india-central"), None)
    assert india_cluster is not None
    assert india_cluster.count == 3
    assert "reg-raipur" in india_cluster.region_ids


def test_map_006_active_layers_enabled_by_default():
    """MAP-006: Map view model includes all standard layer types."""
    vm = build_map_view_model()
    assert GeographyLayerType.REGIONS in vm.active_layers
    assert GeographyLayerType.TRENDS in vm.active_layers
    assert GeographyLayerType.COLLECTIONS in vm.active_layers
    assert GeographyLayerType.PRODUCTS in vm.active_layers


def test_map_007_fashion_map_template_spec():
    """MAP-007: M02 Fashion Map template contains view model and supported regions."""
    spec = get_fashion_map_template("reg-raipur")
    assert spec.screen_id == RegionalScreenId.M02_FASHION_MAP
    assert spec.selected_region is not None
    assert spec.selected_region.id == "reg-raipur"
    assert len(spec.supported_regions) >= 8


def test_map_008_marker_attributes_and_accent():
    """MAP-008: MapMarkerContract carries accent color and item counts."""
    marker = MapMarkerContract(
        id="m-test",
        region_id="reg-raipur",
        title="Test Marker",
        category=MarkerCategory.FEATURED_LOCATION,
        latitude=21.2514,
        longitude=81.6296,
        accent_color="#FF5500",
        item_count=12,
    )
    assert marker.accent_color == "#FF5500"
    assert marker.item_count == 12


def test_map_009_cluster_coordinate_ranges():
    """MAP-009: Cluster coordinates fall within acceptable geographic ranges."""
    clusters = build_map_clusters()
    for c in clusters:
        assert -90.0 <= c.latitude <= 90.0
        assert -180.0 <= c.longitude <= 180.0
        assert c.count >= 2


def test_map_010_viewport_bounding_box_optional():
    """MAP-010: MapViewportContract supports bounding box or None."""
    vp = MapViewportContract(
        center_latitude=10.0,
        center_longitude=20.0,
        zoom_level=5.0,
    )
    assert vp.bounding_box is None


# ===========================================================================
# FORBID-001 to FORBID-008: Extra Fields Forbidden (Constitution Rule I02)
# ===========================================================================

def test_forbid_001_region_contract_extra_field():
    """FORBID-001: RegionContract rejects extra fields."""
    with pytest.raises(ValidationError):
        RegionContract(
            id="reg-invalid",
            name="Invalid",
            type=RegionType.CITY,
            unauthorized_field="illegal",
        )


def test_forbid_002_map_marker_extra_field():
    """FORBID-002: MapMarkerContract rejects extra fields."""
    with pytest.raises(ValidationError):
        MapMarkerContract(
            id="m-invalid",
            region_id="reg-raipur",
            title="Invalid",
            category=MarkerCategory.FEATURED_LOCATION,
            latitude=21.0,
            longitude=81.0,
            rogue_field=123,
        )


def test_forbid_003_map_viewport_extra_field():
    """FORBID-003: MapViewportContract rejects extra fields."""
    with pytest.raises(ValidationError):
        MapViewportContract(
            center_latitude=0.0,
            center_longitude=0.0,
            zoom_level=1.0,
            unexpected="fail",
        )


def test_forbid_004_map_cluster_extra_field():
    """FORBID-004: MapClusterContract rejects extra fields."""
    with pytest.raises(ValidationError):
        MapClusterContract(
            cluster_id="c-invalid",
            count=5,
            latitude=0.0,
            longitude=0.0,
            extra_hack=True,
        )


def test_forbid_005_map_view_model_extra_field():
    """FORBID-005: MapViewModelContract rejects extra fields."""
    vp = MapViewportContract(center_latitude=0.0, center_longitude=0.0, zoom_level=1.0)
    with pytest.raises(ValidationError):
        MapViewModelContract(
            viewport=vp,
            markers=[],
            clusters=[],
            active_layers=[],
            rogue_layer=None,
        )


def test_forbid_006_regional_trend_extra_field():
    """FORBID-006: RegionalTrendContract rejects extra fields."""
    with pytest.raises(ValidationError):
        RegionalTrendContract(
            id="tr-invalid",
            region_id="reg-raipur",
            region_name="Raipur",
            title="Test",
            context_narrative="Desc",
            media_uri="media://test",
            extra_trend_prop=42,
        )


def test_forbid_007_regional_comparison_extra_field():
    """FORBID-007: RegionalComparisonContract rejects extra fields."""
    with pytest.raises(ValidationError):
        RegionalComparisonContract(
            region_ids=[],
            regions=[],
            metrics=[],
            disallowed_key="bad",
        )


def test_forbid_008_screen_template_specs_extra_field():
    """FORBID-008: Screen template specs reject extra fields."""
    with pytest.raises(ValidationError):
        RegionalTrendsTemplateSpecContract(
            screen_id=RegionalScreenId.M07_REGIONAL_TRENDS,
            region=REGIONS_REGISTRY["reg-raipur"],
            trends=[],
            forbidden_attr=True,
        )
