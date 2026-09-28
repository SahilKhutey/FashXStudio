"""Unit tests for FashXStudio Visual Layer Architecture.

Phase 01: Visual Product Architecture
Verifies Screen Inventory, Route Registries, Domain Classifications,
Responsive Breakpoint Models, and Schema Contract integrity (Rules I01, I02, I03).
"""

import pytest
from pydantic import ValidationError

from api.app.features.feature_catalog import FEATURE_CATALOG
from api.app.visual.catalog import (
    BREAKPOINT_CONFIGS,
    CANONICAL_SCREENS,
    get_screen_inventory,
)
from schemas.visual.v1 import (
    BreakpointConfig,
    DeviceBreakpoint,
    NavigationType,
    ScreenDefinition,
    ScreenDomain,
    ScreenInventoryRegistry,
)


def test_screen_inventory_has_expected_volume_and_unique_ids() -> None:
    inventory = get_screen_inventory()
    assert inventory.total_screens == len(CANONICAL_SCREENS)
    assert inventory.total_screens >= 50

    screen_ids = [s.screen_id for s in inventory.screens]
    assert len(screen_ids) == len(set(screen_ids)), "Duplicate screen_id detected!"

    routes = [s.route for s in inventory.screens]
    assert len(routes) == len(set(routes)), "Duplicate route detected!"


def test_all_12_screen_domains_are_covered() -> None:
    inventory = get_screen_inventory()
    registered_domains = {s.domain for s in inventory.screens}
    all_domains = set(ScreenDomain)

    assert registered_domains == all_domains, (
        f"Missing domains in screen inventory: {all_domains - registered_domains}"
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

    # Get by ID
    disc01 = inventory.get_screen("SCR-DISC-01")
    assert disc01 is not None
    assert disc01.title == "Personalized Discovery Feed"
    assert disc01.domain == ScreenDomain.DISCOVERY

    # Get by Route
    route_match = inventory.get_by_route("/(tabs)/tryon")
    assert route_match is not None
    assert route_match.screen_id == "SCR-VTO-01"

    # Get by Domain
    onboarding_screens = inventory.get_by_domain(ScreenDomain.ONBOARDING)
    assert len(onboarding_screens) == 5

    # Non-existent
    assert inventory.get_screen("SCR-DOES-NOT-EXIST") is None
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


def test_biometric_consent_flag_matches_privacy_sensitive_screens() -> None:
    inventory = get_screen_inventory()

    biometric_screens = [s for s in inventory.screens if s.requires_biometric_consent]
    # Biometric consent must be enforced for portrait capture, calibration, VTO fitting canvas, VTO layers, VTO progress, VTO result, avatar manager
    expected_biometric_ids = {
        "SCR-ONB-03",
        "SCR-ONB-04",
        "SCR-VTO-01",
        "SCR-VTO-02",
        "SCR-VTO-03",
        "SCR-VTO-04",
        "SCR-PROF-03",
    }
    actual_biometric_ids = {s.screen_id for s in biometric_screens}
    assert actual_biometric_ids == expected_biometric_ids


def test_visual_design_0_taxonomy_completeness() -> None:
    from schemas.visual.v1 import (
        AiInteractionStage,
        ComponentTaxonomyLevel,
        FashionContentType,
        InteractionStateEnum,
        MapLayerType,
        ShoppingFunnelStage,
    )

    assert len(ComponentTaxonomyLevel) == 4
    assert len(FashionContentType) == 9
    assert len(ShoppingFunnelStage) == 6
    assert len(MapLayerType) == 3
    assert len(AiInteractionStage) == 6
    assert len(InteractionStateEnum) == 12


def test_screen_specification_contract_validates_all_17_fields() -> None:
    from schemas.visual.v1 import InteractionStateEnum, ScreenSpecificationContract

    spec = ScreenSpecificationContract(
        screen_id="SCR-DISC-01",
        screen_name="Personalized Discovery Feed",
        purpose="Deliver MMR λ=0.7 diversified daily outfit recommendations",
        user="Authenticated Consumer",
        entry_point="/(tabs)/discover",
        exit_point="/product/[id], /tryon, /closet",
        primary_action="Select Item for Virtual Try-On",
        secondary_actions=["Save to Closet", "View Stylist Rationale", "Filter by Category"],
        data_sources=["GET /api/v1/recommendations/feed", "GET /api/v1/profile/preferences"],
        components=["ProductGrid", "RecommendationCard", "StylistRationaleChip", "FilterBar"],
        states=[
            InteractionStateEnum.DEFAULT,
            InteractionStateEnum.LOADING,
            InteractionStateEnum.SUCCESS,
            InteractionStateEnum.EMPTY,
            InteractionStateEnum.ERROR,
        ],
        responsive_rules={
            "xs": "Single column vertical feed",
            "sm": "2-column grid",
            "md": "3-column grid",
            "lg": "4-column grid with sticky right try-on canvas",
            "xl": "12-column bounded grid max-width 1440px",
        },
        accessibility={
            "role": "main",
            "aria_label": "Personalized Fashion Discovery Feed",
            "focus_management": "First feed item receives initial keyboard focus",
        },
        error_handling={
            "boundary": "StateBoundary fallback with retry action",
            "envelope": "RFC-7807 ErrorResponse",
        },
        analytics_events=["discovery.opened", "discovery.item_viewed", "discovery.item_saved"],
        dependencies=["FX-F01", "FX-F02", "FX-F03"],
        test_cases=["TC-SCR-DISC-01-01", "TC-SCR-DISC-01-02"],
    )

    assert spec.screen_id == "SCR-DISC-01"
    assert len(spec.secondary_actions) == 3
    assert len(spec.states) == 5

    # Enforce extra="forbid" on 17-point specification contract
    with pytest.raises(ValidationError):
        ScreenSpecificationContract(
            **spec.model_dump(),
            extra_unauthorized_attribute="invalid",
        )
