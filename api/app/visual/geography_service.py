"""Regional Maps & Geography UI Domain Service — Phase 11.

Provides geographic hierarchy, map view models, marker clustering, regional trends,
local product aggregation, and cross-system discovery bridges (Sections 11.1 - 11.105).
"""

from typing import Any
from schemas.visual.fashion import (
    FashionContentType,
    VisualContentModel,
)
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
from .fashion_service import (
    SAMPLE_COLLECTIONS,
    SAMPLE_LOOKS,
    SAMPLE_PRODUCTS,
    SAMPLE_STYLES,
    to_visual_content_model,
)


# ---------------------------------------------------------------------------
# Canonical Geographic Hierarchy Fixtures (Sections 11.3 - 11.5)
# ---------------------------------------------------------------------------

CANONICAL_REGIONS: dict[str, RegionContract] = {
    # --- India Hierarchy ---
    "reg-india": RegionContract(
        id="reg-india",
        name="India",
        type=RegionType.COUNTRY,
        parent_id=None,
        country_code="IN",
        latitude=20.5937,
        longitude=78.9629,
        bounding_box=[68.1, 6.5, 97.4, 37.1],
        timezone="Asia/Kolkata",
        hero_image_uri="https://images.fashx.com/regions/india_hero.jpg",
        description="Rich textile heritage spanning artisanal handlooms, wild silviculture, and emerging streetwear hubs.",
        trends_count=18,
        looks_count=42,
        products_count=320,
        collections_count=14,
        is_supported=True,
    ),
    "reg-chhattisgarh": RegionContract(
        id="reg-chhattisgarh",
        name="Chhattisgarh",
        type=RegionType.STATE,
        parent_id="reg-india",
        country_code="IN",
        state_code="CG",
        latitude=21.2787,
        longitude=81.8661,
        bounding_box=[80.2, 17.7, 84.4, 24.1],
        timezone="Asia/Kolkata",
        hero_image_uri="https://images.fashx.com/regions/chhattisgarh_hero.jpg",
        description="Epicenter of natural golden Kosa wild silk, hand-carved bell metal accessories, and organic tribal weaves.",
        trends_count=4,
        looks_count=8,
        products_count=46,
        collections_count=3,
        is_supported=True,
    ),
    "reg-raipur": RegionContract(
        id="reg-raipur",
        name="Raipur",
        type=RegionType.CITY,
        parent_id="reg-chhattisgarh",
        country_code="IN",
        state_code="CG",
        city_code="RAI",
        latitude=21.2514,
        longitude=81.6296,
        bounding_box=[81.5, 21.1, 81.8, 21.4],
        timezone="Asia/Kolkata",
        hero_image_uri="https://images.fashx.com/regions/raipur_hero.jpg",
        description="Vibrant urban center celebrating natural handloom linen pairings, Dhokra metal accents, and relaxed tailoring.",
        trends_count=3,
        looks_count=6,
        products_count=28,
        collections_count=2,
        is_supported=True,
    ),
    "reg-maharashtra": RegionContract(
        id="reg-maharashtra",
        name="Maharashtra",
        type=RegionType.STATE,
        parent_id="reg-india",
        country_code="IN",
        state_code="MH",
        latitude=19.7515,
        longitude=75.7139,
        bounding_box=[72.6, 15.6, 80.9, 22.0],
        timezone="Asia/Kolkata",
        hero_image_uri="https://images.fashx.com/regions/maharashtra_hero.jpg",
        description="Dynamic commercial capital driving contemporary luxury streetwear, indigo denim culture, and coastal styling.",
        trends_count=8,
        looks_count=24,
        products_count=180,
        collections_count=8,
        is_supported=True,
    ),
    "reg-mumbai": RegionContract(
        id="reg-mumbai",
        name="Mumbai",
        type=RegionType.CITY,
        parent_id="reg-maharashtra",
        country_code="IN",
        state_code="MH",
        city_code="BOM",
        latitude=19.0760,
        longitude=72.8777,
        bounding_box=[72.7, 18.8, 73.1, 19.3],
        timezone="Asia/Kolkata",
        hero_image_uri="https://images.fashx.com/regions/mumbai_hero.jpg",
        description="Coastal metropolis blending humidity-resistant layering with oversized artisanal raw denim aesthetics.",
        trends_count=6,
        looks_count=18,
        products_count=120,
        collections_count=6,
        is_supported=True,
    ),
    "reg-karnataka": RegionContract(
        id="reg-karnataka",
        name="Karnataka",
        type=RegionType.STATE,
        parent_id="reg-india",
        country_code="IN",
        state_code="KA",
        latitude=15.3173,
        longitude=75.7139,
        bounding_box=[74.0, 11.5, 78.6, 18.5],
        timezone="Asia/Kolkata",
        hero_image_uri="https://images.fashx.com/regions/karnataka_hero.jpg",
        description="Innovation corridor combining Mysore Mulberry silk with modern sustainable hemp and weather-adaptive shells.",
        trends_count=5,
        looks_count=12,
        products_count=84,
        collections_count=4,
        is_supported=True,
    ),
    "reg-bengaluru": RegionContract(
        id="reg-bengaluru",
        name="Bengaluru",
        type=RegionType.CITY,
        parent_id="reg-karnataka",
        country_code="IN",
        state_code="KA",
        city_code="BLR",
        latitude=12.9716,
        longitude=77.5946,
        bounding_box=[77.4, 12.8, 77.8, 13.1],
        timezone="Asia/Kolkata",
        hero_image_uri="https://images.fashx.com/regions/bengaluru_hero.jpg",
        description="Garden city tech minimal aesthetic with modular utility garments, relaxed silhouettes, and artisanal cotton.",
        trends_count=4,
        looks_count=10,
        products_count=64,
        collections_count=3,
        is_supported=True,
    ),

    # --- Japan Hierarchy ---
    "reg-japan": RegionContract(
        id="reg-japan",
        name="Japan",
        type=RegionType.COUNTRY,
        parent_id=None,
        country_code="JP",
        latitude=36.2048,
        longitude=138.2529,
        bounding_box=[122.9, 24.0, 153.9, 45.5],
        timezone="Asia/Tokyo",
        hero_image_uri="https://images.fashx.com/regions/japan_hero.jpg",
        description="Pinnacle of vintage shuttle loom selvedge denim, architectural tailoring, and sashiko repair culture.",
        trends_count=12,
        looks_count=36,
        products_count=210,
        collections_count=9,
        is_supported=True,
    ),
    "reg-okayama": RegionContract(
        id="reg-okayama",
        name="Okayama",
        type=RegionType.STATE,
        parent_id="reg-japan",
        country_code="JP",
        state_code="33",
        latitude=34.6618,
        longitude=133.9350,
        bounding_box=[133.3, 34.2, 134.4, 35.3],
        timezone="Asia/Tokyo",
        hero_image_uri="https://images.fashx.com/regions/okayama_hero.jpg",
        description="Global birthplace of premium Japanese denim weaving, indigo dye baths, and bespoke craftsman ateliers.",
        trends_count=6,
        looks_count=16,
        products_count=110,
        collections_count=5,
        is_supported=True,
    ),
    "reg-kojima": RegionContract(
        id="reg-kojima",
        name="Kojima",
        type=RegionType.CITY,
        parent_id="reg-okayama",
        country_code="JP",
        state_code="33",
        city_code="KOJ",
        latitude=34.4667,
        longitude=133.8000,
        bounding_box=[133.7, 34.4, 133.9, 34.5],
        timezone="Asia/Tokyo",
        hero_image_uri="https://images.fashx.com/regions/kojima_hero.jpg",
        description="Famous Denim Street home to family-owned vintage mills crafting 14oz-21oz heavyweight selvedge denim.",
        trends_count=4,
        looks_count=12,
        products_count=78,
        collections_count=4,
        is_supported=True,
    ),

    # --- France Hierarchy ---
    "reg-france": RegionContract(
        id="reg-france",
        name="France",
        type=RegionType.COUNTRY,
        parent_id=None,
        country_code="FR",
        latitude=46.2276,
        longitude=2.2137,
        bounding_box=[-5.1, 41.3, 9.6, 51.1],
        timezone="Europe/Paris",
        hero_image_uri="https://images.fashx.com/regions/france_hero.jpg",
        description="Global epicenter of couture ateliers, structured tailoring, and French flax linen cultivation.",
        trends_count=10,
        looks_count=28,
        products_count=195,
        collections_count=7,
        is_supported=True,
    ),
    "reg-paris": RegionContract(
        id="reg-paris",
        name="Paris",
        type=RegionType.CITY,
        parent_id="reg-france",
        country_code="FR",
        city_code="PAR",
        latitude=48.8566,
        longitude=2.3522,
        bounding_box=[2.2, 48.8, 2.5, 48.9],
        timezone="Europe/Paris",
        hero_image_uri="https://images.fashx.com/regions/paris_hero.jpg",
        description="Understated Parisian elegance balancing fluid wool coats with relaxed monochrome silhouettes.",
        trends_count=7,
        looks_count=20,
        products_count=145,
        collections_count=6,
        is_supported=True,
    ),
}

# In-memory mutable registry
REGIONS_REGISTRY: dict[str, RegionContract] = dict(CANONICAL_REGIONS)


# ---------------------------------------------------------------------------
# Regional Trends Fixtures (Section 11.28)
# ---------------------------------------------------------------------------

REGIONAL_TRENDS_FIXTURES: list[RegionalTrendContract] = [
    RegionalTrendContract(
        id="trend-kosa-linen-drape",
        region_id="reg-raipur",
        region_name="Raipur",
        title="Kosa Wild Silk & Flax Linen Drape",
        context_narrative="Balancing natural golden wild tussar silk with breathable unbleached French flax for high-humidity comfort.",
        momentum="rising",
        media_uri="https://images.fashx.com/trends/kosa_drape.jpg",
        related_product_ids=["prod-linen-02"],
        related_look_ids=["look-mumbai-01"],
    ),
    RegionalTrendContract(
        id="trend-monsoon-streetwear",
        region_id="reg-mumbai",
        region_name="Mumbai",
        title="Coastal Monsoon Layering",
        context_narrative="Fast-drying oversized camp collar shirts paired with heavyweight selvedge denim cuffs for coastal monsoon rain.",
        momentum="surging",
        media_uri="https://images.fashx.com/trends/monsoon_layering.jpg",
        related_product_ids=["prod-denim-01", "prod-linen-02"],
        related_look_ids=["look-mumbai-01"],
    ),
    RegionalTrendContract(
        id="trend-kojima-raw-denim",
        region_id="reg-kojima",
        region_name="Kojima",
        title="Vintage Shuttle Loom Raw Selvedge",
        context_narrative="Unwashed, rope-dyed dark indigo jackets emphasizing authentic fade lines and hand-hammered copper rivets.",
        momentum="established",
        media_uri="https://images.fashx.com/trends/kojima_selvedge.jpg",
        related_product_ids=["prod-denim-01"],
        related_look_ids=["look-mumbai-01"],
    ),
    RegionalTrendContract(
        id="trend-bengaluru-utility",
        region_id="reg-bengaluru",
        region_name="Bengaluru",
        title="Tech Minimal Modular Utility",
        context_narrative="Relaxed boxy fits with concealed magnetic closures, articulated knees, and durable natural fibers.",
        momentum="rising",
        media_uri="https://images.fashx.com/trends/tech_utility.jpg",
        related_product_ids=["prod-linen-02"],
        related_look_ids=["look-mumbai-01"],
    ),
]


# ---------------------------------------------------------------------------
# Map Viewport & Marker Generators (Sections 11.9 - 11.17)
# ---------------------------------------------------------------------------

def build_map_markers(selected_region_id: str | None = None) -> list[MapMarkerContract]:
    """Generate map markers for all supported regions."""
    markers: list[MapMarkerContract] = []
    for reg in REGIONS_REGISTRY.values():
        if reg.latitude is not None and reg.longitude is not None:
            is_sel = reg.id == selected_region_id
            cat = MarkerCategory.REGION if reg.type in (RegionType.COUNTRY, RegionType.STATE) else MarkerCategory.FEATURED_LOCATION
            markers.append(
                MapMarkerContract(
                    id=f"marker-{reg.id}",
                    region_id=reg.id,
                    title=f"{reg.name} ({reg.type.capitalize()})",
                    category=cat,
                    latitude=reg.latitude,
                    longitude=reg.longitude,
                    is_selected=is_sel,
                    accent_color="#111111" if is_sel else "#666666",
                    item_count=reg.products_count,
                )
            )
    return markers


def build_map_clusters() -> list[MapClusterContract]:
    """Generate aggregate clusters for regional markers in close proximity."""
    return [
        MapClusterContract(
            cluster_id="cluster-india-central",
            count=3,
            latitude=21.0,
            longitude=81.0,
            region_ids=["reg-chhattisgarh", "reg-raipur", "reg-maharashtra"],
        ),
        MapClusterContract(
            cluster_id="cluster-japan-west",
            count=2,
            latitude=34.5,
            longitude=133.8,
            region_ids=["reg-okayama", "reg-kojima"],
        ),
    ]


def build_map_view_model(selected_region_id: str | None = None) -> MapViewModelContract:
    """Construct complete map view model for map rendering adapters (Section 11.69)."""
    target = REGIONS_REGISTRY.get(selected_region_id or "reg-india", REGIONS_REGISTRY["reg-india"])
    viewport = MapViewportContract(
        center_latitude=target.latitude or 20.5937,
        center_longitude=target.longitude or 78.9629,
        zoom_level=6.0 if target.type == RegionType.CITY else (4.5 if target.type == RegionType.STATE else 3.5),
        bounding_box=target.bounding_box,
    )
    return MapViewModelContract(
        viewport=viewport,
        markers=build_map_markers(selected_region_id=target.id),
        clusters=build_map_clusters(),
        active_layers=[
            GeographyLayerType.REGIONS,
            GeographyLayerType.TRENDS,
            GeographyLayerType.COLLECTIONS,
            GeographyLayerType.PRODUCTS,
        ],
        selected_region_id=target.id,
        state=GeographyState.READY,
    )


# ---------------------------------------------------------------------------
# Hierarchy & Breadcrumb Engine (Sections 11.3, 11.5, 11.19)
# ---------------------------------------------------------------------------

def get_region_breadcrumbs(region_id: str) -> list[RegionBreadcrumbContract]:
    """Build authoritative hierarchy breadcrumbs from root to leaf (Section 11.19)."""
    crumbs: list[RegionBreadcrumbContract] = []
    current_id: str | None = region_id

    while current_id and current_id in REGIONS_REGISTRY:
        reg = REGIONS_REGISTRY[current_id]
        crumbs.insert(
            0,
            RegionBreadcrumbContract(
                id=reg.id,
                name=reg.name,
                type=reg.type,
                is_current=reg.id == region_id,
            ),
        )
        current_id = reg.parent_id

    return crumbs


def get_child_regions(parent_id: str) -> list[RegionContract]:
    """Retrieve all direct geographic descendants for a parent region."""
    return [r for r in REGIONS_REGISTRY.values() if r.parent_id == parent_id]


# ---------------------------------------------------------------------------
# Screen Template Builders (M01 – M10, Sections 11.6 - 11.24)
# ---------------------------------------------------------------------------

def get_regional_home_template() -> RegionalHomeTemplateSpecContract:
    """Build M01 Regional Home gateway specification (Section 11.6, 11.7)."""
    featured = REGIONS_REGISTRY["reg-india"]
    popular = [
        REGIONS_REGISTRY["reg-raipur"],
        REGIONS_REGISTRY["reg-mumbai"],
        REGIONS_REGISTRY["reg-kojima"],
        REGIONS_REGISTRY["reg-paris"],
    ]

    return RegionalHomeTemplateSpecContract(
        screen_id=RegionalScreenId.M01_REGIONAL_HOME,
        featured_region=featured,
        popular_regions=popular,
        featured_map=build_map_view_model(selected_region_id=featured.id),
        regional_trends=REGIONAL_TRENDS_FIXTURES[:3],
        regional_looks=[to_visual_content_model(l, FashionContentType.LOOK) for l in SAMPLE_LOOKS],
        local_products=[to_visual_content_model(p, FashionContentType.PRODUCT) for p in SAMPLE_PRODUCTS],
        regional_collections=[to_visual_content_model(c, FashionContentType.COLLECTION) for c in SAMPLE_COLLECTIONS],
    )


def get_fashion_map_template(region_id: str | None = None) -> FashionMapTemplateSpecContract:
    """Build M02 Fashion Map interactive interface specification (Section 11.8)."""
    target = REGIONS_REGISTRY.get(region_id or "reg-raipur", REGIONS_REGISTRY["reg-raipur"])
    return FashionMapTemplateSpecContract(
        screen_id=RegionalScreenId.M02_FASHION_MAP,
        map_view=build_map_view_model(selected_region_id=target.id),
        selected_region=target,
        available_layers=[
            GeographyLayerType.REGIONS,
            GeographyLayerType.TRENDS,
            GeographyLayerType.COLLECTIONS,
            GeographyLayerType.PRODUCTS,
        ],
        supported_regions=list(REGIONS_REGISTRY.values()),
    )


def get_regional_explorer_template(
    parent_id: str | None = None,
    query: str = "",
) -> RegionalExplorerTemplateSpecContract:
    """Build M03 Regional Explorer list & text browsing canvas (Section 11.25, 11.26)."""
    if query:
        matched = [r for r in REGIONS_REGISTRY.values() if query.lower() in r.name.lower()]
        return RegionalExplorerTemplateSpecContract(
            screen_id=RegionalScreenId.M03_REGIONAL_EXPLORER,
            breadcrumbs=[],
            regions=matched,
            active_search_query=query,
            parent_region=None,
        )

    if parent_id and parent_id in REGIONS_REGISTRY:
        parent = REGIONS_REGISTRY[parent_id]
        children = get_child_regions(parent.id)
        return RegionalExplorerTemplateSpecContract(
            screen_id=RegionalScreenId.M03_REGIONAL_EXPLORER,
            breadcrumbs=get_region_breadcrumbs(parent.id),
            regions=children,
            active_search_query="",
            parent_region=parent,
        )

    # Top-level countries
    countries = [r for r in REGIONS_REGISTRY.values() if r.type == RegionType.COUNTRY]
    return RegionalExplorerTemplateSpecContract(
        screen_id=RegionalScreenId.M03_REGIONAL_EXPLORER,
        breadcrumbs=[],
        regions=countries,
        active_search_query="",
        parent_region=None,
    )


def get_country_template(country_id: str) -> CountryTemplateSpecContract:
    """Build M04 Country View template specification (Section 11.20)."""
    country = REGIONS_REGISTRY.get(country_id, REGIONS_REGISTRY["reg-india"])
    states = get_child_regions(country.id)
    trends = [t for t in REGIONAL_TRENDS_FIXTURES if country.name.lower() in t.context_narrative.lower() or country.name.lower() in t.region_name.lower()]
    if not trends:
        trends = REGIONAL_TRENDS_FIXTURES[:2]

    return CountryTemplateSpecContract(
        screen_id=RegionalScreenId.M04_COUNTRY_VIEW,
        country=country,
        breadcrumbs=get_region_breadcrumbs(country.id),
        states_or_provinces=states,
        regional_trends=trends,
        popular_styles=[to_visual_content_model(s, FashionContentType.STYLE) for s in SAMPLE_STYLES],
        local_products=[to_visual_content_model(p, FashionContentType.PRODUCT) for p in SAMPLE_PRODUCTS],
        curated_looks=[to_visual_content_model(l, FashionContentType.LOOK) for l in SAMPLE_LOOKS],
    )


def get_state_template(state_id: str) -> StateTemplateSpecContract:
    """Build M05 State / Province View template specification (Section 11.22)."""
    state = REGIONS_REGISTRY.get(state_id, REGIONS_REGISTRY["reg-chhattisgarh"])
    parent = REGIONS_REGISTRY.get(state.parent_id or "reg-india", REGIONS_REGISTRY["reg-india"])
    cities = get_child_regions(state.id)
    trends = [t for t in REGIONAL_TRENDS_FIXTURES if t.region_id == state.id or any(c.id == t.region_id for c in cities)]
    if not trends:
        trends = [REGIONAL_TRENDS_FIXTURES[0]]

    return StateTemplateSpecContract(
        screen_id=RegionalScreenId.M05_STATE_VIEW,
        state_region=state,
        country_region=parent,
        breadcrumbs=get_region_breadcrumbs(state.id),
        cities=cities,
        regional_trends=trends,
        local_products=[to_visual_content_model(p, FashionContentType.PRODUCT) for p in SAMPLE_PRODUCTS],
        curated_looks=[to_visual_content_model(l, FashionContentType.LOOK) for l in SAMPLE_LOOKS],
    )


def get_city_template(city_id: str) -> CityTemplateSpecContract:
    """Build M06 City View template specification (Section 11.23)."""
    city = REGIONS_REGISTRY.get(city_id, REGIONS_REGISTRY["reg-raipur"])
    trends = [t for t in REGIONAL_TRENDS_FIXTURES if t.region_id == city.id]
    if not trends:
        trends = [REGIONAL_TRENDS_FIXTURES[0]]

    related = [r for r in REGIONS_REGISTRY.values() if r.type == RegionType.CITY and r.id != city.id][:3]

    return CityTemplateSpecContract(
        screen_id=RegionalScreenId.M06_CITY_VIEW,
        city=city,
        breadcrumbs=get_region_breadcrumbs(city.id),
        local_areas=[],
        fashion_trends=trends,
        local_products=[to_visual_content_model(p, FashionContentType.PRODUCT) for p in SAMPLE_PRODUCTS],
        local_looks=[to_visual_content_model(l, FashionContentType.LOOK) for l in SAMPLE_LOOKS],
        related_cities=related,
    )


def get_regional_trends_template(region_id: str) -> RegionalTrendsTemplateSpecContract:
    """Build M07 Regional Trends template specification (Section 11.28)."""
    region = REGIONS_REGISTRY.get(region_id, REGIONS_REGISTRY["reg-raipur"])
    trends = [t for t in REGIONAL_TRENDS_FIXTURES if t.region_id == region.id]
    if not trends:
        trends = REGIONAL_TRENDS_FIXTURES[:2]

    return RegionalTrendsTemplateSpecContract(
        screen_id=RegionalScreenId.M07_REGIONAL_TRENDS,
        region=region,
        trends=trends,
    )


def get_local_products_template(region_id: str) -> LocalProductsTemplateSpecContract:
    """Build M08 Local Products template specification (Section 11.30)."""
    region = REGIONS_REGISTRY.get(region_id, REGIONS_REGISTRY["reg-raipur"])
    products = [to_visual_content_model(p, FashionContentType.PRODUCT) for p in SAMPLE_PRODUCTS]

    return LocalProductsTemplateSpecContract(
        screen_id=RegionalScreenId.M08_LOCAL_PRODUCTS,
        region=region,
        products=products,
        total_count=len(products),
        available_filters=["Textile: Kosa Silk", "Textile: Selvedge Denim", "In Stock", "Price: Under ₹5,000"],
    )


def get_regional_collections_template(region_id: str) -> RegionalCollectionsTemplateSpecContract:
    """Build M09 Regional Collections template specification (Section 11.32)."""
    region = REGIONS_REGISTRY.get(region_id, REGIONS_REGISTRY["reg-raipur"])
    colls = [to_visual_content_model(c, FashionContentType.COLLECTION) for c in SAMPLE_COLLECTIONS]

    return RegionalCollectionsTemplateSpecContract(
        screen_id=RegionalScreenId.M09_REGIONAL_COLLECTIONS,
        region=region,
        featured_collection=colls[0],
        collections=colls,
    )


def get_location_detail_template(location_id: str) -> LocationDetailTemplateSpecContract:
    """Build M10 Location Detail template specification (Section 11.24)."""
    loc = REGIONS_REGISTRY.get(location_id, REGIONS_REGISTRY["reg-raipur"])
    trends = [t for t in REGIONAL_TRENDS_FIXTURES if t.region_id == loc.id]
    if not trends:
        trends = REGIONAL_TRENDS_FIXTURES[:1]

    return LocationDetailTemplateSpecContract(
        screen_id=RegionalScreenId.M10_LOCATION_DETAIL,
        location=loc,
        breadcrumbs=get_region_breadcrumbs(loc.id),
        map_view=build_map_view_model(selected_region_id=loc.id),
        trends=trends,
        products=[to_visual_content_model(p, FashionContentType.PRODUCT) for p in SAMPLE_PRODUCTS],
        looks=[to_visual_content_model(l, FashionContentType.LOOK) for l in SAMPLE_LOOKS],
    )


# ---------------------------------------------------------------------------
# Regional Search & Comparison Engine (Sections 11.27, 11.46)
# ---------------------------------------------------------------------------

def search_regions(query: str = "", region_type: RegionType | None = None) -> list[RegionContract]:
    """Execute search across regions filtering by title and entity classification."""
    results: list[RegionContract] = []
    q_lower = query.lower()
    for reg in REGIONS_REGISTRY.values():
        if query and q_lower not in reg.name.lower() and q_lower not in (reg.description or "").lower():
            continue
        if region_type and reg.type != region_type:
            continue
        results.append(reg)
    return results


def compare_regions(region_ids: list[str]) -> RegionalComparisonContract:
    """Build factual side-by-side geographic fashion comparison matrix (Section 11.46)."""
    regions = [REGIONS_REGISTRY[rid] for rid in region_ids if rid in REGIONS_REGISTRY]
    if not regions:
        regions = [REGIONS_REGISTRY["reg-raipur"], REGIONS_REGISTRY["reg-mumbai"]]

    metrics = [
        RegionalComparisonMetricContract(
            name="Primary Textile Craft",
            values_by_region={
                "reg-raipur": "Kosa Wild Silk & Dhokra Bell Metal",
                "reg-mumbai": "14oz Selvedge Denim & Flax Linen",
                "reg-kojima": "Japanese Vintage Shuttle Loom Denim",
                "reg-paris": "Couture Tailoring & Fine Wool",
            },
        ),
        RegionalComparisonMetricContract(
            name="Climate & Silhouette Alignment",
            values_by_region={
                "reg-raipur": "High Heat / Fluid Boxy Handlooms",
                "reg-mumbai": "Coastal Monsoon / Humidity-Resistant Layers",
                "reg-kojima": "Temperate Coastal / Heavyweight Workwear",
                "reg-paris": "Temperate Continental / Structured Coats",
            },
        ),
        RegionalComparisonMetricContract(
            name="Catalog Density (Products / Looks)",
            values_by_region={r.id: f"{r.products_count} Products • {r.looks_count} Looks" for r in regions},
        ),
    ]

    return RegionalComparisonContract(
        region_ids=[r.id for r in regions],
        regions=regions,
        metrics=metrics,
    )


def reset_geography_fixtures() -> None:
    """Reset mutable in-memory geography registry for test isolation."""
    global REGIONS_REGISTRY
    REGIONS_REGISTRY = dict(CANONICAL_REGIONS)
