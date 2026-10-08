"""Unit tests for Responsive & Adaptive Visual System — Phase 14.

Verifies:
- RESP-001: Breakpoint resolution across layout thresholds (XS, SM, MD, LG, XL, 2XL)
- RESP-002: Container sizing, margins, padding, and bounded widths
- RESP-003: Dynamic fluid grid column calculations and boundary conditions
- RESP-004: Typography adaptation and semantic token mapping
- RESP-005: Spacing adaptation and padding resolution
- RESP-006: Visibility rules and P0-P3 priority framework
- RESP-007: Navigation adaptation (Sidebar vs Compact vs BottomNav/Drawer)
- RESP-008: Card adaptation and metadata pruning
- RESP-009: Filter adaptation (Sidebar vs Button vs Bottom Sheet)
- RESP-010: Modal adaptation (Centered vs Bottom Sheet)
- RESP-011: Drawer and sheet presentation logic
- RESP-012: Safe area boundaries and sticky action preservation
- RESP-013: Extreme viewports (320px small mobile, 2560px ultra-wide containment)
- RESP-014: Orientation handling (Portrait vs Landscape)
- FORBID-001 to FORBID-008: Strict extra="forbid" rejection across all Responsive contracts (Constitution Rule I02).
"""

import pytest
from pydantic import ValidationError

from schemas.visual.responsive import (
    CardContentPruningRequest,
    CardContentPruningResult,
    CheckoutLayoutType,
    ContentPriorityLevel,
    CrossSystemScreenResponsiveContract,
    DeviceOrientation,
    FilterAdaptationType,
    InteractionInputMode,
    LayoutMode,
    MapLayoutType,
    ModalAdaptationType,
    NavigationAdaptationType,
    OutfitBuilderLayoutType,
    ResponsiveBreakpoint,
    ResponsiveContainerContract,
    ResponsiveGridCalculationRequest,
    ResponsiveGridCalculationResult,
    SafeAreaInsetsContract,
    TypographyScaleToken,
    ViewportEvaluationRequest,
    ViewportEvaluationResult,
)
from fashx.visual.responsive_service import (
    CONTAINER_CONFIGS,
    calculate_fluid_grid,
    evaluate_viewport,
    get_cross_system_screen_qa,
    prune_card_content,
    resolve_breakpoint,
    resolve_container_config,
    resolve_layout_mode,
)


# ---------------------------------------------------------------------------
# RESP-001: Breakpoint Resolution
# ---------------------------------------------------------------------------

def test_resp_001_breakpoint_resolution() -> None:
    """RESP-001: Viewport widths resolve strictly into established layout thresholds (Section 14.3)."""
    assert resolve_breakpoint(320) == ResponsiveBreakpoint.XS
    assert resolve_breakpoint(479) == ResponsiveBreakpoint.XS
    assert resolve_breakpoint(480) == ResponsiveBreakpoint.SM
    assert resolve_breakpoint(767) == ResponsiveBreakpoint.SM
    assert resolve_breakpoint(768) == ResponsiveBreakpoint.MD
    assert resolve_breakpoint(1023) == ResponsiveBreakpoint.MD
    assert resolve_breakpoint(1024) == ResponsiveBreakpoint.LG
    assert resolve_breakpoint(1279) == ResponsiveBreakpoint.LG
    assert resolve_breakpoint(1280) == ResponsiveBreakpoint.XL
    assert resolve_breakpoint(1535) == ResponsiveBreakpoint.XL
    assert resolve_breakpoint(1536) == ResponsiveBreakpoint.XXL
    assert resolve_breakpoint(2560) == ResponsiveBreakpoint.XXL


def test_resp_001_layout_mode_resolution() -> None:
    """RESP-001: 3-way layout mode (compact, adaptive, expanded) resolves correctly (Section 14.4)."""
    assert resolve_layout_mode(360) == LayoutMode.COMPACT
    assert resolve_layout_mode(767) == LayoutMode.COMPACT
    assert resolve_layout_mode(768) == LayoutMode.ADAPTIVE
    assert resolve_layout_mode(1023) == LayoutMode.ADAPTIVE
    assert resolve_layout_mode(1024) == LayoutMode.EXPANDED
    assert resolve_layout_mode(1920) == LayoutMode.EXPANDED


# ---------------------------------------------------------------------------
# RESP-002: Container Sizing & Padding
# ---------------------------------------------------------------------------

def test_resp_002_container_sizing_and_padding() -> None:
    """RESP-002: Container configs enforce semantic padding and max widths (Section 14.5 - 14.7)."""
    c_xs = resolve_container_config(ResponsiveBreakpoint.XS)
    assert c_xs.horizontal_padding_px == 16
    assert c_xs.gutter_px == 12
    assert c_xs.container_max_width_px == 480
    assert c_xs.default_columns == 4

    c_md = resolve_container_config(ResponsiveBreakpoint.MD)
    assert c_md.horizontal_padding_px == 24
    assert c_md.gutter_px == 20
    assert c_md.container_max_width_px == 960
    assert c_md.default_columns == 8

    c_xl = resolve_container_config(ResponsiveBreakpoint.XL)
    assert c_xl.horizontal_padding_px == 32
    assert c_xl.gutter_px == 24
    assert c_xl.container_max_width_px == 1440
    assert c_xl.default_columns == 12

    c_2xl = resolve_container_config(ResponsiveBreakpoint.XXL)
    assert c_2xl.horizontal_padding_px == 32
    assert c_2xl.gutter_px == 32
    assert c_2xl.container_max_width_px == 1600


# ---------------------------------------------------------------------------
# RESP-003: Dynamic Fluid Grid Calculation
# ---------------------------------------------------------------------------

def test_resp_003_fluid_grid_calculation() -> None:
    """RESP-003: Dynamic fluid grid computes optimal columns and card widths (Section 14.8 - 14.10)."""
    # Desktop 1200px container with 280px minimum card
    req_desktop = ResponsiveGridCalculationRequest(
        available_width_px=1200,
        card_min_width_px=280,
        gap_px=16,
    )
    res_desktop = calculate_fluid_grid(req_desktop)
    assert res_desktop.computed_columns == 4
    assert res_desktop.card_width_px > 280.0
    assert res_desktop.utilization_pct == 100.0

    # Mobile 360px container
    req_mobile = ResponsiveGridCalculationRequest(
        available_width_px=360,
        card_min_width_px=280,
        gap_px=12,
    )
    res_mobile = calculate_fluid_grid(req_mobile)
    assert res_mobile.computed_columns == 1
    assert res_mobile.card_width_px == 360.0

    # Narrow constraint below card min width clamps to 1 column
    req_narrow = ResponsiveGridCalculationRequest(
        available_width_px=240,
        card_min_width_px=280,
        gap_px=12,
    )
    res_narrow = calculate_fluid_grid(req_narrow)
    assert res_narrow.computed_columns == 1
    assert res_narrow.card_width_px == 240.0


# ---------------------------------------------------------------------------
# RESP-004: Typography Adaptation
# ---------------------------------------------------------------------------

def test_resp_004_typography_tokens() -> None:
    """RESP-004: Typography scale tokens adhere to semantic hierarchy (Section 14.19)."""
    assert TypographyScaleToken.DISPLAY_XL == "display_xl"
    assert TypographyScaleToken.DISPLAY_L == "display_l"
    assert TypographyScaleToken.DISPLAY_M == "display_m"
    assert TypographyScaleToken.HEADING_XL == "heading_xl"
    assert TypographyScaleToken.BODY_M == "body_m"


# ---------------------------------------------------------------------------
# RESP-005: Spacing Adaptation
# ---------------------------------------------------------------------------

def test_resp_005_spacing_adaptation() -> None:
    """RESP-005: Spacing scales smoothly without arbitrary offsets (Section 14.22)."""
    for bp in ResponsiveBreakpoint:
        cfg = CONTAINER_CONFIGS[bp]
        assert cfg.horizontal_padding_px in [16, 24, 32]
        assert cfg.gutter_px in [12, 16, 20, 24, 32]


# ---------------------------------------------------------------------------
# RESP-006 & RESP-008: Card Adaptation & Priority Pruning (P0-P3)
# ---------------------------------------------------------------------------

def test_resp_006_card_priority_compact_pruning() -> None:
    """RESP-006: In compact mode, P2 (specs) and P3 (tags) are pruned (Section 14.28)."""
    req = CardContentPruningRequest(
        layout_mode=LayoutMode.COMPACT,
        image_url="https://images.fashx.studio/prod1.jpg",
        title="Oversized Denim Jacket",
        primary_action_label="Add to Bag",
        brand="Studio FashX",
        price_formatted="$240.00",
        availability="In Stock",
        secondary_specs={"Material": "100% Selvedge", "Origin": "Japan"},
        tags=["Minimalist", "Oversized", "Autumn"],
    )
    res = prune_card_content(req)
    # P0 and P1 are rendered
    assert "image_url" in res.rendered_fields
    assert "title" in res.rendered_fields
    assert "brand" in res.rendered_fields
    assert "price_formatted" in res.rendered_fields
    assert "availability" in res.rendered_fields
    # P2 and P3 are pruned on compact
    assert "secondary_specs" in res.pruned_fields
    assert "tags" in res.pruned_fields
    assert res.display_brand is True
    assert res.display_price is True
    assert res.display_secondary_specs is False
    assert res.display_tags is False
    assert res.touch_target_min_px >= 44


def test_resp_008_card_priority_expanded_full_metadata() -> None:
    """RESP-008: In expanded mode, all P0, P1, P2, and P3 metadata are rendered (Section 14.28)."""
    req = CardContentPruningRequest(
        layout_mode=LayoutMode.EXPANDED,
        image_url="https://images.fashx.studio/prod1.jpg",
        title="Oversized Denim Jacket",
        primary_action_label="Add to Bag",
        brand="Studio FashX",
        price_formatted="$240.00",
        availability="In Stock",
        secondary_specs={"Material": "100% Selvedge", "Origin": "Japan"},
        tags=["Minimalist", "Oversized", "Autumn"],
    )
    res = prune_card_content(req)
    assert "secondary_specs" in res.rendered_fields
    assert "tags" in res.rendered_fields
    assert res.display_secondary_specs is True
    assert res.display_tags is True
    assert len(res.pruned_fields) == 0


def test_resp_008_card_priority_adaptive_metadata() -> None:
    """RESP-008: In adaptive mode, P2 is rendered but P3 is pruned (Section 14.28)."""
    req = CardContentPruningRequest(
        layout_mode=LayoutMode.ADAPTIVE,
        image_url="https://images.fashx.studio/prod1.jpg",
        title="Oversized Denim Jacket",
        primary_action_label="Add to Bag",
        brand="Studio FashX",
        price_formatted="$240.00",
        availability="In Stock",
        secondary_specs={"Material": "100% Selvedge"},
        tags=["Minimalist"],
    )
    res = prune_card_content(req)
    assert res.display_secondary_specs is True
    assert res.display_tags is False
    assert "tags" in res.pruned_fields


# ---------------------------------------------------------------------------
# RESP-007: Navigation Adaptation
# ---------------------------------------------------------------------------

def test_resp_007_navigation_adaptation() -> None:
    """RESP-007: Navigation structure transforms across viewports (Section 14.15)."""
    compact_eval = evaluate_viewport(
        ViewportEvaluationRequest(width_px=390, height_px=844)
    )
    assert compact_eval.navigation_adaptation == NavigationAdaptationType.MOBILE_BOTTOM_NAV_DRAWER

    adaptive_eval = evaluate_viewport(
        ViewportEvaluationRequest(width_px=820, height_px=1180)
    )
    assert adaptive_eval.navigation_adaptation == NavigationAdaptationType.TABLET_COMPACT_SIDEBAR

    expanded_eval = evaluate_viewport(
        ViewportEvaluationRequest(width_px=1440, height_px=900)
    )
    assert expanded_eval.navigation_adaptation == NavigationAdaptationType.DESKTOP_SIDEBAR


# ---------------------------------------------------------------------------
# RESP-009 & RESP-010: Filter & Modal Adaptation
# ---------------------------------------------------------------------------

def test_resp_009_filter_and_modal_adaptation() -> None:
    """RESP-009 & 010: Filters and modals adapt to bottom sheets vs centered/sidebars (Section 14.29 & 14.53)."""
    # Compact
    c_eval = evaluate_viewport(ViewportEvaluationRequest(width_px=375, height_px=667))
    assert c_eval.filter_adaptation == FilterAdaptationType.BOTTOM_SHEET_FILTER
    assert c_eval.modal_adaptation == ModalAdaptationType.BOTTOM_SHEET

    # Adaptive
    a_eval = evaluate_viewport(ViewportEvaluationRequest(width_px=800, height_px=1000))
    assert a_eval.filter_adaptation == FilterAdaptationType.FILTER_BUTTON_DRAWER
    assert a_eval.modal_adaptation == ModalAdaptationType.CENTERED_MODAL

    # Expanded
    e_eval = evaluate_viewport(ViewportEvaluationRequest(width_px=1400, height_px=900))
    assert e_eval.filter_adaptation == FilterAdaptationType.SIDEBAR_FILTERS
    assert e_eval.modal_adaptation == ModalAdaptationType.CENTERED_MODAL


# ---------------------------------------------------------------------------
# RESP-011: Specialized Canvas Layouts (Builder, Map, Checkout)
# ---------------------------------------------------------------------------

def test_resp_011_specialized_canvas_layouts() -> None:
    """RESP-011: Outfit builder, map, and checkout layouts adapt correctly (Section 14.35, 14.40, 14.44)."""
    # Mobile
    m_eval = evaluate_viewport(ViewportEvaluationRequest(width_px=400, height_px=800))
    assert m_eval.outfit_builder_layout == OutfitBuilderLayoutType.MOBILE_CANVAS_SHEET
    assert m_eval.map_layout == MapLayoutType.MOBILE_MAP_BOTTOM_SHEET
    assert m_eval.checkout_layout == CheckoutLayoutType.MOBILE_ACCORDION_STICKY

    # Tablet
    t_eval = evaluate_viewport(ViewportEvaluationRequest(width_px=900, height_px=1200))
    assert t_eval.outfit_builder_layout == OutfitBuilderLayoutType.TABLET_2_COLUMN
    assert t_eval.map_layout == MapLayoutType.DESKTOP_SIDE_RESULTS
    assert t_eval.checkout_layout == CheckoutLayoutType.DESKTOP_2_COLUMN

    # Desktop
    d_eval = evaluate_viewport(ViewportEvaluationRequest(width_px=1600, height_px=1000))
    assert d_eval.outfit_builder_layout == OutfitBuilderLayoutType.DESKTOP_3_COLUMN
    assert d_eval.map_layout == MapLayoutType.DESKTOP_SIDE_RESULTS
    assert d_eval.checkout_layout == CheckoutLayoutType.DESKTOP_2_COLUMN


# ---------------------------------------------------------------------------
# RESP-012: Safe Area & Sticky Actions
# ---------------------------------------------------------------------------

def test_resp_012_safe_area_and_touch() -> None:
    """RESP-012: Safe area insets and touch baselines are respected (Section 14.14 & 14.48)."""
    insets = SafeAreaInsetsContract(top_px=47, bottom_px=34, left_px=0, right_px=0)
    ev = evaluate_viewport(
        ViewportEvaluationRequest(
            width_px=390,
            height_px=844,
            input_mode=InteractionInputMode.TOUCH,
            safe_area_insets=insets,
        )
    )
    assert ev.safe_area_insets.top_px == 47
    assert ev.safe_area_insets.bottom_px == 34
    assert ev.touch_target_px >= 44
    assert ev.is_touch is True
    assert ev.supports_hover is False


# ---------------------------------------------------------------------------
# RESP-013: Extreme Viewports
# ---------------------------------------------------------------------------

def test_resp_013_extreme_viewports() -> None:
    """RESP-013: Small 320px viewport and 2560px ultra-wide viewports are bounded (Section 14.57 & 14.59)."""
    # 320px small mobile
    small_eval = evaluate_viewport(ViewportEvaluationRequest(width_px=320, height_px=568))
    assert small_eval.breakpoint == ResponsiveBreakpoint.XS
    assert small_eval.layout_mode == LayoutMode.COMPACT
    assert small_eval.body_max_width_px == 320

    # 2560px ultra-wide
    wide_eval = evaluate_viewport(ViewportEvaluationRequest(width_px=2560, height_px=1440))
    assert wide_eval.breakpoint == ResponsiveBreakpoint.XXL
    assert wide_eval.layout_mode == LayoutMode.EXPANDED
    # Max container constraint prevents uncontrolled text stretching (Section 14.59)
    assert wide_eval.body_max_width_px == 1600


# ---------------------------------------------------------------------------
# RESP-014: Orientation Handling
# ---------------------------------------------------------------------------

def test_resp_014_orientation_handling() -> None:
    """RESP-014: Orientation dynamically resolves to landscape or portrait (Section 14.56 & 14.87)."""
    portrait_eval = evaluate_viewport(ViewportEvaluationRequest(width_px=390, height_px=844))
    assert portrait_eval.orientation == DeviceOrientation.PORTRAIT

    landscape_eval = evaluate_viewport(ViewportEvaluationRequest(width_px=844, height_px=390))
    assert landscape_eval.orientation == DeviceOrientation.LANDSCAPE


# ---------------------------------------------------------------------------
# Cross-System Screen QA Tests (VD-03 to VD-13)
# ---------------------------------------------------------------------------

def test_resp_cross_system_screen_qa() -> None:
    """RESP-CROSS: Validates representative screens from all prior visual phases (Section 14.94)."""
    # VD-09 Product Detail (P02) has sticky actions on mobile
    p02_mobile = get_cross_system_screen_qa("P02", width_px=390)
    assert p02_mobile.layout_mode == LayoutMode.COMPACT
    assert p02_mobile.has_sticky_actions is True

    p02_desktop = get_cross_system_screen_qa("P02", width_px=1440)
    assert p02_desktop.layout_mode == LayoutMode.EXPANDED
    assert p02_desktop.has_sticky_actions is False

    # VD-10 Outfit Builder (ST02)
    st02 = get_cross_system_screen_qa("ST02", width_px=390)
    assert st02.domain == "style"
    assert st02.modal_presentation == ModalAdaptationType.BOTTOM_SHEET

    # VD-11 Regional Map (M02)
    m02 = get_cross_system_screen_qa("M02", width_px=390)
    assert m02.domain == "regional"
    assert m02.filter_presentation == FilterAdaptationType.BOTTOM_SHEET_FILTER

    # VD-12 AI Assistant (AI02)
    ai02 = get_cross_system_screen_qa("AI02", width_px=390)
    assert ai02.domain == "ai"
    assert ai02.has_sticky_actions is True

    # VD-13 Preferences (PR08)
    pr08 = get_cross_system_screen_qa("PR08", width_px=390)
    assert pr08.domain == "profile"
    assert pr08.has_sticky_actions is True


# ---------------------------------------------------------------------------
# Constitution Rule I02: extra="forbid" Rejection Tests
# ---------------------------------------------------------------------------

def test_forbid_001_container_contract() -> None:
    """FORBID-001: ResponsiveContainerContract forbids extra fields."""
    with pytest.raises(ValidationError):
        ResponsiveContainerContract(
            breakpoint=ResponsiveBreakpoint.XS,
            min_width_px=0,
            container_max_width_px=480,
            horizontal_padding_px=16,
            gutter_px=12,
            default_columns=4,
            unauthorized_field="illegal",  # type: ignore
        )


def test_forbid_002_grid_request() -> None:
    """FORBID-002: ResponsiveGridCalculationRequest forbids extra fields."""
    with pytest.raises(ValidationError):
        ResponsiveGridCalculationRequest(
            available_width_px=1000,
            invalid_prop=123,  # type: ignore
        )


def test_forbid_003_grid_result() -> None:
    """FORBID-003: ResponsiveGridCalculationResult forbids extra fields."""
    with pytest.raises(ValidationError):
        ResponsiveGridCalculationResult(
            available_width_px=1000,
            computed_columns=4,
            card_width_px=235.0,
            gap_px=16,
            utilization_pct=100.0,
            bogus="extra",  # type: ignore
        )


def test_forbid_004_card_pruning_request() -> None:
    """FORBID-004: CardContentPruningRequest forbids extra fields."""
    with pytest.raises(ValidationError):
        CardContentPruningRequest(
            layout_mode=LayoutMode.COMPACT,
            image_url="test.jpg",
            title="Test",
            primary_action_label="Action",
            extra_field="nope",  # type: ignore
        )


def test_forbid_005_card_pruning_result() -> None:
    """FORBID-005: CardContentPruningResult forbids extra fields."""
    with pytest.raises(ValidationError):
        CardContentPruningResult(
            layout_mode=LayoutMode.COMPACT,
            rendered_fields=[],
            pruned_fields=[],
            display_brand=True,
            display_price=True,
            display_availability=True,
            display_secondary_specs=False,
            display_tags=False,
            touch_target_min_px=44,
            unknown_arg="blocked",  # type: ignore
        )


def test_forbid_006_safe_area_insets() -> None:
    """FORBID-006: SafeAreaInsetsContract forbids extra fields."""
    with pytest.raises(ValidationError):
        SafeAreaInsetsContract(top_px=20, extra="illegal")  # type: ignore


def test_forbid_007_viewport_request() -> None:
    """FORBID-007: ViewportEvaluationRequest forbids extra fields."""
    with pytest.raises(ValidationError):
        ViewportEvaluationRequest(width_px=500, height_px=800, hack=True)  # type: ignore


def test_forbid_008_cross_system_contract() -> None:
    """FORBID-008: CrossSystemScreenResponsiveContract forbids extra fields."""
    with pytest.raises(ValidationError):
        CrossSystemScreenResponsiveContract(
            screen_id="P01",
            domain="shopping",
            title="Product Listing",
            layout_mode=LayoutMode.COMPACT,
            active_navigation=NavigationAdaptationType.MOBILE_BOTTOM_NAV_DRAWER,
            content_density="compact",
            has_sticky_actions=False,
            modal_presentation=ModalAdaptationType.BOTTOM_SHEET,
            filter_presentation=FilterAdaptationType.BOTTOM_SHEET_FILTER,
            accessible_reading_order_preserved=True,
            touch_target_compliant=True,
            horizontal_overflow_prevented=True,
            illegal="rejected",  # type: ignore
        )
