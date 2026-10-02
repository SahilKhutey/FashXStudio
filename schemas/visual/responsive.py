"""FashXStudio Responsive & Adaptive Visual System Contracts — Version 1.

Defines the mathematical, spatial, viewport, layout, navigation, grid, component priority,
and interaction adaptation contracts for Phase 14 (VD-14 Responsive / Adaptive Visual System).
Adheres strictly to Constitution Rule I02 (Contract Primacy) with extra="forbid".
All tokens and breakpoints integrate with the established FashXStudio design token system.
"""

from enum import StrEnum
from typing import Any
from pydantic import Field
from schemas.base import BaseContractModel


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class ResponsiveBreakpoint(StrEnum):
    """Layout thresholds established in Section 14.3 (not merely device names)."""
    XS = "xs"    # < 480px (Compact Mobile)
    SM = "sm"    # >= 480px (Large Mobile / Phablet)
    MD = "md"    # >= 768px (Tablet Portrait)
    LG = "lg"    # >= 1024px (Tablet Landscape / Laptop)
    XL = "xl"    # >= 1280px (Desktop)
    XXL = "2xl"  # >= 1536px (Large Desktop / Ultra-Wide)


class LayoutMode(StrEnum):
    """Semantic layout modes driving component adaptation (Section 14.4 & 14.116)."""
    COMPACT = "compact"    # Mobile viewport (< 768px)
    ADAPTIVE = "adaptive"  # Tablet viewport (768px - 1023px)
    EXPANDED = "expanded"  # Desktop & Ultra-wide (>= 1024px)


class InteractionInputMode(StrEnum):
    """Input capabilities of the active client (Section 14.1 & 14.49)."""
    TOUCH = "touch"
    MOUSE = "mouse"
    KEYBOARD = "keyboard"
    POINTER = "pointer"


class DeviceOrientation(StrEnum):
    """Physical or viewport orientation (Section 14.56 & 14.87)."""
    PORTRAIT = "portrait"
    LANDSCAPE = "landscape"


class ContentPriorityLevel(StrEnum):
    """Content classification framework for responsive degradation (Section 14.28 & 14.66)."""
    P0_REQUIRED = "p0_required"      # Image, Name, Primary Action
    P1_IMPORTANT = "p1_important"    # Brand, Price, Availability
    P2_SUPPORTING = "p2_supporting"  # Secondary metadata, specs, rating
    P3_OPTIONAL = "p3_optional"      # Extended tags, badges, decorative notes


class NavigationAdaptationType(StrEnum):
    """Structural navigation pattern based on available space (Section 14.15 - 14.18)."""
    DESKTOP_SIDEBAR = "desktop_sidebar"
    TABLET_COMPACT_SIDEBAR = "tablet_compact_sidebar"
    MOBILE_BOTTOM_NAV_DRAWER = "mobile_bottom_nav_drawer"


class ModalAdaptationType(StrEnum):
    """Modal and sheet adaptation patterns (Section 14.53 - 14.55)."""
    CENTERED_MODAL = "centered_modal"
    RIGHT_DRAWER = "right_drawer"
    BOTTOM_SHEET = "bottom_sheet"
    FULL_SCREEN = "full_screen"


class FilterAdaptationType(StrEnum):
    """Filter presentation across viewports (Section 14.29 & 14.30)."""
    SIDEBAR_FILTERS = "sidebar_filters"
    FILTER_BUTTON_DRAWER = "filter_button_drawer"
    BOTTOM_SHEET_FILTER = "bottom_sheet_filter"


class OutfitBuilderLayoutType(StrEnum):
    """Styling studio 3-way layout adaptation (Section 14.35 & 14.36)."""
    DESKTOP_3_COLUMN = "desktop_3_column"          # Browser | Canvas | Inspector
    TABLET_2_COLUMN = "tablet_2_column"            # Browser | Canvas (Inspector at bottom)
    MOBILE_CANVAS_SHEET = "mobile_canvas_sheet"    # Canvas with Bottom Sheet drawers


class MapLayoutType(StrEnum):
    """Regional fashion map layout adaptation (Section 14.40 - 14.42)."""
    DESKTOP_SIDE_RESULTS = "desktop_side_results"  # Sidebar filters/results + Map canvas
    MOBILE_MAP_BOTTOM_SHEET = "mobile_map_bottom_sheet"  # Full map + floating filter + bottom sheet


class CheckoutLayoutType(StrEnum):
    """Commercial checkout adaptation (Section 14.44 & 14.45)."""
    DESKTOP_2_COLUMN = "desktop_2_column"          # Checkout Steps | Order Summary
    MOBILE_ACCORDION_STICKY = "mobile_accordion_sticky"  # Sequential Accordion + Sticky Summary


class TypographyScaleToken(StrEnum):
    """Semantic typography scaling token mappings (Section 14.19)."""
    DISPLAY_XL = "display_xl"
    DISPLAY_L = "display_l"
    DISPLAY_M = "display_m"
    HEADING_XL = "heading_xl"
    HEADING_L = "heading_l"
    HEADING_M = "heading_m"
    HEADING_S = "heading_s"
    BODY_L = "body_l"
    BODY_M = "body_m"
    BODY_S = "body_s"
    CAPTION = "caption"


# ---------------------------------------------------------------------------
# Structural & Mathematical Contracts
# ---------------------------------------------------------------------------

class SafeAreaInsetsContract(BaseContractModel):
    """Mobile safe-area boundary constraints (Section 14.14)."""
    top_px: int = Field(default=0, ge=0, description="Top safe-area inset (status bar, notch)")
    bottom_px: int = Field(default=0, ge=0, description="Bottom safe-area inset (home gesture bar)")
    left_px: int = Field(default=0, ge=0, description="Left safe-area inset (landscape camera cutouts)")
    right_px: int = Field(default=0, ge=0, description="Right safe-area inset")


class ResponsiveContainerContract(BaseContractModel):
    """Container responsibilities and padding boundaries (Section 14.5 - 14.7)."""
    breakpoint: ResponsiveBreakpoint = Field(..., description="Target breakpoint")
    min_width_px: int = Field(..., ge=0, description="Minimum viewport width")
    max_width_px: int | None = Field(default=None, description="Maximum viewport width or None for infinite")
    container_max_width_px: int = Field(..., gt=0, description="Maximum bounded content width")
    horizontal_padding_px: int = Field(..., ge=0, description="Semantic page horizontal padding")
    gutter_px: int = Field(..., ge=0, description="Column gutter spacing")
    default_columns: int = Field(..., ge=1, le=16, description="Base column count")


class ResponsiveGridCalculationRequest(BaseContractModel):
    """Fluid grid calculation input parameters (Section 14.8 - 14.10)."""
    available_width_px: int = Field(..., gt=0, description="Available container width in pixels")
    card_min_width_px: int = Field(default=280, gt=50, description="Minimum viable card width")
    gap_px: int = Field(default=16, ge=0, description="Gap spacing between columns")
    max_columns: int = Field(default=12, ge=1, le=16, description="Upper column ceiling")


class ResponsiveGridCalculationResult(BaseContractModel):
    """Computed fluid grid metrics avoiding breakpoint-heavy code (Section 14.10)."""
    available_width_px: int = Field(..., description="Supplied container width")
    computed_columns: int = Field(..., ge=1, description="Calculated number of columns")
    card_width_px: float = Field(..., gt=0, description="Calculated card width in pixels")
    gap_px: int = Field(..., description="Applied gap spacing")
    utilization_pct: float = Field(..., ge=0.0, le=100.0, description="Container width utilization percentage")


class CardContentPruningRequest(BaseContractModel):
    """Component metadata pruning evaluation input (Section 14.27 & 14.28)."""
    layout_mode: LayoutMode = Field(..., description="Active layout mode")
    image_url: str = Field(..., description="Product or look image URL")
    title: str = Field(..., description="Primary title / product name")
    primary_action_label: str = Field(..., description="Primary CTA e.g. Add to Bag")
    brand: str | None = Field(default=None, description="Brand name (P1)")
    price_formatted: str | None = Field(default=None, description="Formatted price (P1)")
    availability: str | None = Field(default=None, description="Stock status (P1)")
    secondary_specs: dict[str, str] = Field(default_factory=dict, description="Specs e.g. fabric, fit (P2)")
    tags: list[str] = Field(default_factory=list, description="Optional style tags (P3)")


class CardContentPruningResult(BaseContractModel):
    """Pruned card metadata respecting content priority model (Section 14.28)."""
    layout_mode: LayoutMode = Field(..., description="Evaluated layout mode")
    rendered_fields: list[str] = Field(..., description="Fields retained for visual display")
    pruned_fields: list[str] = Field(..., description="Fields omitted or collapsed into overflow")
    touch_target_min_px: int = Field(default=44, ge=44, description="WCAG 2.1 AA touch target baseline")
    display_brand: bool = Field(default=True)
    display_price: bool = Field(default=True)
    display_availability: bool = Field(default=True)
    display_secondary_specs: bool = Field(default=False)
    display_tags: bool = Field(default=False)


# ---------------------------------------------------------------------------
# Master Responsive Viewport Evaluation Contracts
# ---------------------------------------------------------------------------

class ViewportEvaluationRequest(BaseContractModel):
    """Comprehensive viewport assessment parameters (Section 14.1 & 14.88)."""
    width_px: int = Field(..., gt=0, description="Current viewport width in pixels")
    height_px: int = Field(..., gt=0, description="Current viewport height in pixels")
    input_mode: InteractionInputMode = Field(default=InteractionInputMode.TOUCH)
    prefers_reduced_motion: bool = Field(default=False, description="User prefers-reduced-motion setting")
    text_zoom_factor: float = Field(default=1.0, ge=1.0, le=3.0, description="Browser or system zoom factor")
    safe_area_insets: SafeAreaInsetsContract = Field(default_factory=SafeAreaInsetsContract)


class ViewportEvaluationResult(BaseContractModel):
    """The master responsive decision model output (Section 14.4 & 14.88)."""
    width_px: int
    height_px: int
    breakpoint: ResponsiveBreakpoint
    layout_mode: LayoutMode
    orientation: DeviceOrientation
    navigation_adaptation: NavigationAdaptationType
    modal_adaptation: ModalAdaptationType
    filter_adaptation: FilterAdaptationType
    outfit_builder_layout: OutfitBuilderLayoutType
    map_layout: MapLayoutType
    checkout_layout: CheckoutLayoutType
    container_config: ResponsiveContainerContract
    body_max_width_px: int
    touch_target_px: int = Field(default=44)
    supports_hover: bool
    is_compact: bool
    is_adaptive: bool
    is_expanded: bool
    is_touch: bool
    is_reduced_motion: bool
    safe_area_insets: SafeAreaInsetsContract


# ---------------------------------------------------------------------------
# Cross-System Screen Responsiveness QA Contract
# ---------------------------------------------------------------------------

class CrossSystemScreenResponsiveContract(BaseContractModel):
    """Validation contract verifying responsive adaptation across all prior phases (Section 14.94)."""
    screen_id: str = Field(..., description="Screen catalog ID e.g. P02, ST02, M02, AI02, PR02")
    domain: str = Field(..., description="Screen domain classification")
    title: str = Field(..., description="Human-readable screen title")
    layout_mode: LayoutMode = Field(..., description="Evaluated layout mode")
    active_navigation: NavigationAdaptationType = Field(..., description="Applied navigation structure")
    content_density: str = Field(..., description="Applied density token e.g. comfortable, compact, spacious")
    has_sticky_actions: bool = Field(default=False, description="Whether sticky purchase/actions bar is active")
    modal_presentation: ModalAdaptationType = Field(..., description="How dialogs/sheets present in this mode")
    filter_presentation: FilterAdaptationType = Field(..., description="How filtering presents in this mode")
    accessible_reading_order_preserved: bool = Field(default=True, description="DOM order equals logical reading order")
    touch_target_compliant: bool = Field(default=True, description="All interactive controls >= 44px")
    horizontal_overflow_prevented: bool = Field(default=True, description="No unhandled horizontal scroll traps")
