"""Unit tests for FashXStudio Visual Layer Architecture.

Phase 01: Visual Product Architecture + Complete Screen / Page Inventory
Verifies Screen Inventory (123 screens), Route Registries, Domain Classifications,
Page Templates (11 templates), Implementation Dependency Groups (5 groups),
Responsive Breakpoint Models, and Schema Contract integrity (Rules I01, I02, I03).
"""

import pytest
from pydantic import ValidationError

from fashx.features.feature_catalog import FEATURE_CATALOG
from fashx.visual.catalog import (
    BREAKPOINT_CONFIGS,
    CANONICAL_SCREENS,
    get_screen_inventory,
)
from schemas.visual.v1 import (
    BreakpointConfig,
    DeviceBreakpoint,
    ImplementationDependencyGroup,
    NavigationType,
    PageTemplateType,
    ScreenDefinition,
    ScreenDomain,
    ScreenInventoryRegistry,
)


def test_screen_inventory_has_exact_123_screens_and_unique_ids() -> None:
    inventory = get_screen_inventory()
    assert inventory.total_screens == 123
    assert len(CANONICAL_SCREENS) == 123

    screen_ids = [s.screen_id for s in inventory.screens]
    assert len(screen_ids) == len(set(screen_ids)), "Duplicate screen_id detected!"

    routes = [s.route for s in inventory.screens]
    assert len(routes) == len(set(routes)), "Duplicate route detected!"


def test_all_13_screen_domains_are_covered() -> None:
    inventory = get_screen_inventory()
    registered_domains = {s.domain for s in inventory.screens}

    core_domains = {
        ScreenDomain.PLATFORM,
        ScreenDomain.HOME,
        ScreenDomain.DISCOVERY,
        ScreenDomain.SEARCH,
        ScreenDomain.PRODUCT,
        ScreenDomain.SHOPPING,
        ScreenDomain.FASHION,
        ScreenDomain.STYLE,
        ScreenDomain.TRENDS,
        ScreenDomain.REGIONAL,
        ScreenDomain.AI,
        ScreenDomain.PROFILE,
        ScreenDomain.SYSTEM,
    }

    assert core_domains == registered_domains, (
        f"Missing or mismatched domains: {core_domains ^ registered_domains}"
    )


def test_all_11_page_templates_are_covered() -> None:
    inventory = get_screen_inventory()
    registered_templates = {s.template_type for s in inventory.screens}
    all_templates = set(PageTemplateType)

    assert registered_templates == all_templates, (
        f"Missing templates in screen inventory: {all_templates - registered_templates}"
    )


def test_all_5_implementation_dependency_groups_are_covered() -> None:
    inventory = get_screen_inventory()
    registered_groups = {s.dependency_group for s in inventory.screens}
    all_groups = set(ImplementationDependencyGroup)

    assert registered_groups == all_groups, (
        f"Missing dependency groups in screen inventory: {all_groups - registered_groups}"
    )


def test_every_screen_references_valid_feature_catalog_id() -> None:
    inventory = get_screen_inventory()
    valid_feature_ids = {f.feature_id for f in FEATURE_CATALOG}

    for screen in inventory.screens:
        assert screen.feature_id in valid_feature_ids, (
            f"Screen {screen.screen_id} has unbound feature_id '{screen.feature_id}'"
        )


def test_screen_lookup_helpers() -> None:
    inventory = get_screen_inventory()

    # Get by ID / Code
    p02 = inventory.get_screen("P02")
    assert p02 is not None
    assert p02.title == "Product Detail"
    assert p02.domain == ScreenDomain.PRODUCT
    assert p02.template_type == PageTemplateType.DETAIL

    # Get by Route
    route_match = inventory.get_by_route("/(tabs)/discover")
    assert route_match is not None
    assert route_match.screen_id == "D01"

    # Get by Domain
    home_screens = inventory.get_by_domain(ScreenDomain.HOME)
    assert len(home_screens) == 7

    # Get by Template
    listing_screens = inventory.get_by_template(PageTemplateType.LISTING)
    assert len(listing_screens) >= 30

    # Get by Dependency Group
    group_a_screens = inventory.get_by_dependency_group(ImplementationDependencyGroup.GROUP_A_FOUNDATION)
    assert len(group_a_screens) == 8

    # Non-existent
    assert inventory.get_screen("Z99") is None
    assert inventory.get_by_route("/non/existent") is None


def test_breakpoint_configurations_and_coverage() -> None:
    assert len(BREAKPOINT_CONFIGS) == 5
    bps = [b.breakpoint for b in BREAKPOINT_CONFIGS]
    assert bps == [
        DeviceBreakpoint.XS,
        DeviceBreakpoint.SM,
        DeviceBreakpoint.MD,
        DeviceBreakpoint.LG,
        DeviceBreakpoint.XL,
    ]

    # Verify column progression
    cols = [b.columns for b in BREAKPOINT_CONFIGS]
    assert cols == [4, 6, 8, 12, 12]

    # Verify monotonic minimum width progression
    min_widths = [b.min_width for b in BREAKPOINT_CONFIGS]
    assert min_widths == sorted(min_widths)


def test_schema_contract_primacy_rejects_extra_fields() -> None:
    with pytest.raises(ValidationError):
        ScreenDefinition(
            screen_id="SCR-TEST-01",
            title="Invalid Extra Fields Screen",
            domain=ScreenDomain.DISCOVERY,
            route="/test/extra",
            navigation_type=NavigationType.STACK,
            feature_id="FX-F03",
            extra_unauthorized_field="illegal_payload",  # Should trigger extra='forbid'
        )


def test_visual_design_0_taxonomy_completeness() -> None:
    from schemas.visual.v1 import (
        AiInteractionStage,
        ComponentTaxonomyLevel,
        FashionContentType,
        ImplementationDependencyGroup,
        InteractionStateEnum,
        MapLayerType,
        PageTemplateType,
        ShoppingFunnelStage,
    )

    assert len(ComponentTaxonomyLevel) == 4
    assert len(FashionContentType) == 9
    assert len(ShoppingFunnelStage) == 6
    assert len(MapLayerType) == 3
    assert len(AiInteractionStage) == 6
    assert len(InteractionStateEnum) == 12
    assert len(PageTemplateType) == 11
    assert len(ImplementationDependencyGroup) == 5


def test_screen_specification_contract_validates_all_17_fields() -> None:
    from schemas.visual.v1 import InteractionStateEnum, ScreenSpecificationContract

    spec = ScreenSpecificationContract(
        screen_id="P02",
        screen_name="Product Detail",
        purpose="Deliver comprehensive single-garment inspection with gallery and variant swatches",
        user="Authenticated / Guest Consumer",
        entry_point="/products, /discover, /search",
        exit_point="/products, /tryon, /shopping/cart",
        primary_action="Launch Virtual Try-On",
        secondary_actions=["Add to Cart", "Save to Wishlist", "View Sizing Guide"],
        data_sources=["GET /api/v1/products/{id}", "GET /api/v1/products/{id}/availability"],
        components=["HeroGallery", "SpecSheet", "VariantPicker", "PriceComponent"],
        states=[
            InteractionStateEnum.DEFAULT,
            InteractionStateEnum.LOADING,
            InteractionStateEnum.SUCCESS,
            InteractionStateEnum.EMPTY,
            InteractionStateEnum.ERROR,
        ],
        responsive_rules={
            "xs": "Single column scrollable vertical stack",
            "sm": "Enlarged hero image with sticky bottom action sheet",
            "md": "Split pane: 50% gallery left, 50% product info right",
            "lg": "Split pane with sticky styling canvas on right rail",
            "xl": "Bounded 12-column grid max-width 1440px",
        },
        accessibility={
            "role": "main",
            "aria_label": "Product Detail Page",
            "focus_management": "Gallery receives initial focus on mount",
        },
        error_handling={
            "boundary": "StateBoundary fallback with retry action",
            "envelope": "RFC-7807 ErrorResponse",
        },
        analytics_events=["product.viewed", "product.variant_selected", "product.action"],
        dependencies=["FX-F01", "FX-F05"],
        test_cases=["TC-P02-01", "TC-P02-02"],
    )

    assert spec.screen_id == "P02"
    assert len(spec.secondary_actions) == 3
    assert len(spec.states) == 5

    with pytest.raises(ValidationError):
        ScreenSpecificationContract(
            **spec.model_dump(),
            extra_unauthorized_attribute="invalid",
        )
