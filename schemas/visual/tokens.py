"""FashXStudio Design Token System Contracts — Version 1.

Defines the mathematical, typographic, spatial, colorimetric, and behavioral contracts
for the FashXStudio design token system (Phase 02).
Adheres strictly to Constitution Rule I02 (Contract Primacy) with extra="forbid".
All tokens follow the strict 3-tier hierarchy: Primitive -> Semantic -> Component.
"""

from enum import StrEnum
from typing import Any
from pydantic import Field
from schemas.base import BaseContractModel


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class ThemeMode(StrEnum):
    LIGHT = "light"
    DARK = "dark"


class DensityMode(StrEnum):
    COMFORTABLE = "comfortable"
    COMPACT = "compact"
    SPACIOUS = "spacious"


class ImageAspect(StrEnum):
    SQUARE = "1:1"
    PORTRAIT = "3:4"
    LANDSCAPE = "16:9"
    EDITORIAL = "2:3"
    PRODUCT = "3:4"


class ImageFit(StrEnum):
    COVER = "cover"
    CONTAIN = "contain"


# ---------------------------------------------------------------------------
# 1. Color System: Primitives, MST, Brand, Status, Domains
# ---------------------------------------------------------------------------

class NeutralColorPrimitives(BaseContractModel):
    """12-point neutral structural scale for surfaces, borders, and typography."""
    neutral_0: str = Field(default="#FFFFFF", description="Absolute white")
    neutral_50: str = Field(default="#F9FAFB", description="Soft canvas background")
    neutral_100: str = Field(default="#F3F4F6", description="Subtle surface background")
    neutral_200: str = Field(default="#E5E7EB", description="Subtle border and divider")
    neutral_300: str = Field(default="#D1D5DB", description="Default border")
    neutral_400: str = Field(default="#9CA3AF", description="Muted icon and placeholder")
    neutral_500: str = Field(default="#6B7280", description="Tertiary content")
    neutral_600: str = Field(default="#4B5563", description="Secondary content")
    neutral_700: str = Field(default="#374151", description="Strong border and text")
    neutral_800: str = Field(default="#1F2937", description="Primary dark element")
    neutral_900: str = Field(default="#111827", description="Primary content text")
    neutral_950: str = Field(default="#030712", description="Obsidian black background")


class MonkSkinTonePalette(BaseContractModel):
    """Monk Skin Tone (MST) 10-point inclusive calibration scale & undertones."""
    mst_01: str = Field(default="#F6EDE4", description="Monk scale tone 1")
    mst_02: str = Field(default="#F3E7DB", description="Monk scale tone 2")
    mst_03: str = Field(default="#F7DAD0", description="Monk scale tone 3")
    mst_04: str = Field(default="#EADABA", description="Monk scale tone 4")
    mst_05: str = Field(default="#D7BD96", description="Monk scale tone 5")
    mst_06: str = Field(default="#A07E56", description="Monk scale tone 6")
    mst_07: str = Field(default="#825C43", description="Monk scale tone 7")
    mst_08: str = Field(default="#604134", description="Monk scale tone 8")
    mst_09: str = Field(default="#3A312A", description="Monk scale tone 9")
    mst_10: str = Field(default="#292420", description="Monk scale tone 10")
    undertone_warm: str = Field(default="#E0A96D", description="Warm undertone calibration")
    undertone_cool: str = Field(default="#D4AFCD", description="Cool undertone calibration")
    undertone_neutral: str = Field(default="#C8B89E", description="Neutral undertone calibration")


class BrandColorPalette(BaseContractModel):
    """Configurable brand identity palette (Section 2.4)."""
    primary: str = Field(default="#0F172A", description="Obsidian Luxury Black / Deep Slate")
    primary_hover: str = Field(default="#1E293B", description="Hover state for primary action")
    primary_active: str = Field(default="#020617", description="Active/pressed state for primary action")
    secondary: str = Field(default="#6366F1", description="Electric Indigo AI accent")
    accent: str = Field(default="#E11D48", description="Rose Couture fashion accent")


class StatusColorPalette(BaseContractModel):
    """Semantic status signaling colors and background surfaces (Section 2.5)."""
    success: str = Field(default="#10B981", description="Success signal (saved / completed)")
    success_surface: str = Field(default="#ECFDF5", description="Success light surface tint")
    warning: str = Field(default="#F59E0B", description="Warning signal (limited stock)")
    warning_surface: str = Field(default="#FFFBEB", description="Warning light surface tint")
    error: str = Field(default="#EF4444", description="Error signal (failed action)")
    error_surface: str = Field(default="#FEF2F2", description="Error light surface tint")
    info: str = Field(default="#3B82F6", description="Info signal (system notification)")
    info_surface: str = Field(default="#EFF6FF", description="Info light surface tint")


class DomainColorPalette(BaseContractModel):
    """Domain-specific visual semantic accents (Section 2.6)."""
    product: str = Field(default="#0F172A", description="Commercial product surfaces")
    fashion: str = Field(default="#8B5CF6", description="Editorial fashion & runway")
    shopping: str = Field(default="#10B981", description="Cart, checkout, commerce")
    trend: str = Field(default="#EC4899", description="Trend intelligence signals")
    ai: str = Field(default="#6366F1", description="AI stylist rationale & insights")
    geography: str = Field(default="#0EA5E9", description="Regional maps & climate")


class SemanticSurfaces(BaseContractModel):
    """Semantic surface roles (Section 2.3)."""
    primary: str = Field(..., description="Main page background canvas")
    secondary: str = Field(..., description="Card, panel, secondary container")
    tertiary: str = Field(..., description="Elevated card or nested panel")
    inverse: str = Field(..., description="Inverse contrast container")
    elevated: str = Field(..., description="Floating modal, drawer, or sheet")


class SemanticContent(BaseContractModel):
    """Semantic content (text, icons) roles (Section 2.3)."""
    primary: str = Field(..., description="Primary body and heading text")
    secondary: str = Field(..., description="Secondary metadata and captions")
    tertiary: str = Field(..., description="Tertiary hints and placeholders")
    inverse: str = Field(..., description="Text against inverse backgrounds")
    disabled: str = Field(..., description="Disabled or inactive content")


class SemanticBorders(BaseContractModel):
    """Semantic border roles (Section 2.3 & 2.17)."""
    default: str = Field(..., description="Standard card and divider border")
    subtle: str = Field(..., description="Subtle separation border")
    strong: str = Field(..., description="Prominent active container outline")
    focus: str = Field(..., description="Focus indicator border")
    error: str = Field(..., description="Validation error border")


class SemanticActions(BaseContractModel):
    """Semantic action state colors (Section 2.35)."""
    primary: str = Field(..., description="Primary call-to-action fill")
    primary_hover: str = Field(..., description="Hover state for primary action")
    primary_text: str = Field(..., description="Text on primary call-to-action")
    secondary: str = Field(..., description="Secondary button fill")
    secondary_hover: str = Field(..., description="Secondary button hover")
    secondary_text: str = Field(..., description="Text on secondary button")
    destructive: str = Field(..., description="Destructive action fill/text")
    ghost: str = Field(..., description="Transparent ghost button background")


# ---------------------------------------------------------------------------
# 2. Typography System
# ---------------------------------------------------------------------------

class TypeScaleToken(BaseContractModel):
    """Typography scale entry with fluid sizing and optical tracking (Section 2.7 & 2.8)."""
    size_px: int = Field(..., ge=8, le=96, description="Font size in pixels")
    line_height_px: int = Field(..., ge=10, le=120, description="Line height in pixels")
    letter_spacing_em: float = Field(default=0.0, description="Optical tracking adjustment in em")
    weight: int = Field(default=400, description="Default font weight (400, 500, 600, 700)")


class TypographyFamilyTokens(BaseContractModel):
    """Font family stacks (Section 2.10)."""
    display: str = Field(default="'Playfair Display', 'Didot', serif", description="Editorial / luxury display serif")
    heading: str = Field(default="'Plus Jakarta Sans', 'Inter', sans-serif", description="Modern geometric heading sans")
    body: str = Field(default="'Inter', -apple-system, BlinkMacSystemFont, sans-serif", description="High-legibility body sans")
    ui: str = Field(default="'Plus Jakarta Sans', 'Inter', sans-serif", description="Optimized UI control typography")
    mono: str = Field(default="'JetBrains Mono', 'Fira Code', monospace", description="Data, prices, codes, specs")


class FontWeightTokens(BaseContractModel):
    """Font weights (Section 2.11)."""
    regular: int = Field(default=400)
    medium: int = Field(default=500)
    semibold: int = Field(default=600)
    bold: int = Field(default=700)


class LineHeightTokens(BaseContractModel):
    """Relative line heights (Section 2.12)."""
    tight: float = Field(default=1.15, description="Editorial headings")
    snug: float = Field(default=1.25, description="Cards and compact headings")
    normal: float = Field(default=1.45, description="Default UI text")
    relaxed: float = Field(default=1.65, description="Long-form editorial reading")


class TypographyScaleCatalog(BaseContractModel):
    """The 14 canonical typography tokens from Section 2.8."""
    display_xl: TypeScaleToken = Field(..., description="48px Major landing hero")
    display_l: TypeScaleToken = Field(..., description="40px Large editorial heading")
    display_m: TypeScaleToken = Field(..., description="32px Feature heading")
    heading_xl: TypeScaleToken = Field(..., description="28px Page heading")
    heading_l: TypeScaleToken = Field(..., description="24px Section heading")
    heading_m: TypeScaleToken = Field(..., description="20px Card/group heading")
    heading_s: TypeScaleToken = Field(..., description="18px Compact heading")
    body_l: TypeScaleToken = Field(..., description="17px Prominent editorial body")
    body_m: TypeScaleToken = Field(..., description="16px Default body copy")
    body_s: TypeScaleToken = Field(..., description="14px Supporting / card body")
    label_l: TypeScaleToken = Field(..., description="14px Button & primary control label")
    label_m: TypeScaleToken = Field(..., description="12px Secondary control label")
    label_s: TypeScaleToken = Field(..., description="11px Compact tag/chip label")
    caption: TypeScaleToken = Field(..., description="12px Image caption / metadata")
    overline: TypeScaleToken = Field(..., description="11px Uppercase eyebrow category")


# ---------------------------------------------------------------------------
# 3. Spacing, Sizing, Targets
# ---------------------------------------------------------------------------

class SpacingScale(BaseContractModel):
    """4px base increment spacing matrix (Section 2.13)."""
    space_1: int = Field(default=4)
    space_2: int = Field(default=8)
    space_3: int = Field(default=12)
    space_4: int = Field(default=16)
    space_5: int = Field(default=20)
    space_6: int = Field(default=24)
    space_8: int = Field(default=32)
    space_10: int = Field(default=40)
    space_12: int = Field(default=48)
    space_16: int = Field(default=64)
    space_20: int = Field(default=80)
    space_24: int = Field(default=96)


class SemanticSpacing(BaseContractModel):
    """Semantic spacing hierarchy (Section 2.14)."""
    inline: int = Field(default=8, description="Between inline icons and text")
    element: int = Field(default=12, description="Between elements within a component")
    component: int = Field(default=16, description="Between adjacent components")
    section: int = Field(default=32, description="Between distinct layout sections")
    page: int = Field(default=48, description="Page outer margins and hero spacing")


class SizingScale(BaseContractModel):
    """Component standard heights/sizes (Section 2.15)."""
    xs: int = Field(default=24, description="Small badge / indicator")
    sm: int = Field(default=32, description="Compact icon button / tag")
    md: int = Field(default=40, description="Standard input / button")
    lg: int = Field(default=48, description="Prominent touch button")
    xl: int = Field(default=56, description="Hero action / major control")


class TargetSizeTokens(BaseContractModel):
    """Accessibility minimum touch targets (Section 2.16 & WCAG 2.5.5/2.5.8)."""
    compact_desktop_min_px: int = Field(default=36, description="Compact desktop target")
    primary_control_min_px: int = Field(default=40, description="Primary control target")
    touch_target_min_px: int = Field(default=44, description="WCAG mobile touch target minimum")


# ---------------------------------------------------------------------------
# 4. Geometry: Borders, Radii, Shadows, Elevation, Opacity, Z-Index
# ---------------------------------------------------------------------------

class BorderWidthTokens(BaseContractModel):
    """Border width primitives (Section 2.17)."""
    none: int = Field(default=0)
    thin: int = Field(default=1)
    medium: int = Field(default=2)
    strong: int = Field(default=3)


class RadiusScale(BaseContractModel):
    """Border radius scale (Section 2.18)."""
    none: int = Field(default=0)
    xs: int = Field(default=4, description="Tags, chips, subtle inner rounding")
    sm: int = Field(default=6, description="Input fields, buttons")
    md: int = Field(default=10, description="Cards, notifications")
    lg: int = Field(default=14, description="Dialogs, sheets, modals")
    xl: int = Field(default=20, description="Floating action trays, hero banners")
    full: int = Field(default=9999, description="Pills, avatar circles")


class ElevationTokens(BaseContractModel):
    """Elevation shadow levels (Section 2.19)."""
    elevation_0: str = Field(default="none", description="Flat level 0")
    elevation_1: str = Field(default="0 1px 3px rgba(0, 0, 0, 0.08), 0 1px 2px rgba(0, 0, 0, 0.04)", description="Card elevation")
    elevation_2: str = Field(default="0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)", description="Dropdown / Drawer")
    elevation_3: str = Field(default="0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)", description="Floating Panel")
    elevation_4: str = Field(default="0 20px 25px -5px rgba(0, 0, 0, 0.12), 0 10px 10px -5px rgba(0, 0, 0, 0.04)", description="Modal / Dialog")


class OpacityTokens(BaseContractModel):
    """Opacity tokens (Section 2.20)."""
    disabled: float = Field(default=0.38)
    muted: float = Field(default=0.60)
    overlay: float = Field(default=0.75)
    scrim: float = Field(default=0.85)


class ZIndexTokens(BaseContractModel):
    """Centralized z-index layers preventing arbitrary z-index 9999 (Section 2.21)."""
    base: int = Field(default=0)
    sticky: int = Field(default=100)
    dropdown: int = Field(default=200)
    overlay: int = Field(default=300)
    modal: int = Field(default=400)
    popover: int = Field(default=500)
    toast: int = Field(default=600)
    max: int = Field(default=9999)


# ---------------------------------------------------------------------------
# 5. Responsive, Grid, Container
# ---------------------------------------------------------------------------

class BreakpointPixels(BaseContractModel):
    """Breakpoint boundary thresholds in pixels (Section 2.22)."""
    xs_max: int = Field(default=479)
    sm: int = Field(default=480)
    md: int = Field(default=768)
    lg: int = Field(default=1024)
    xl: int = Field(default=1280)
    two_xl: int = Field(default=1536)


class ContainerMaxWidths(BaseContractModel):
    """Container maximum content widths in pixels (Section 2.23)."""
    sm: int = Field(default=640)
    md: int = Field(default=768)
    lg: int = Field(default=1024)
    xl: int = Field(default=1280)
    two_xl: int = Field(default=1536)
    full: str = Field(default="100%")


class GridTokens(BaseContractModel):
    """Grid layout column and gutter specifications (Section 2.24)."""
    desktop_columns: int = Field(default=12)
    tablet_columns: int = Field(default=8)
    mobile_columns: int = Field(default=4)
    gutter_mobile: int = Field(default=16)
    gutter_tablet: int = Field(default=24)
    gutter_desktop: int = Field(default=32)
    product_min_card_width_px: int = Field(default=240, description="Minimum card width for adaptive grid calculation (Section 2.25)")


# ---------------------------------------------------------------------------
# 6. Motion, Easing, Accessibility Focus
# ---------------------------------------------------------------------------

class MotionDurationTokens(BaseContractModel):
    """Animation durations in milliseconds (Section 2.28)."""
    instant_ms: int = Field(default=50)
    fast_ms: int = Field(default=150)
    normal_ms: int = Field(default=250)
    slow_ms: int = Field(default=400)


class MotionEasingTokens(BaseContractModel):
    """Cubic bezier easing curves (Section 2.29)."""
    standard: str = Field(default="cubic-bezier(0.4, 0.0, 0.2, 1)")
    enter: str = Field(default="cubic-bezier(0.0, 0.0, 0.2, 1)")
    exit: str = Field(default="cubic-bezier(0.4, 0.0, 1.0, 1)")
    emphasized: str = Field(default="cubic-bezier(0.2, 0.0, 0.0, 1)")


class ReducedMotionTokens(BaseContractModel):
    """Accessibility reduced-motion override contract (Section 2.30)."""
    duration_ms: int = Field(default=0, description="Instantaneous animation duration")
    easing: str = Field(default="linear", description="Linear motion curve")


class FocusTokens(BaseContractModel):
    """Keyboard visible focus indicator tokens (Section 2.31)."""
    ring_color: str = Field(default="#6366F1", description="Electric Indigo focus ring")
    width_px: int = Field(default=2, description="2px high-visibility outline")
    offset_px: int = Field(default=2, description="2px offset from element edge")


class DensityScaleMultipliers(BaseContractModel):
    """Density multipliers for spacing and padding (Section 2.39)."""
    compact: float = Field(default=0.8, description="Compact data/shopping density")
    comfortable: float = Field(default=1.0, description="Standard consumer density")
    spacious: float = Field(default=1.25, description="Spacious editorial density")


# ---------------------------------------------------------------------------
# 7. Component Token Model (Section 2.34 & 2.41)
# ---------------------------------------------------------------------------

class ProductCardComponentTokens(BaseContractModel):
    """Concrete token mapping for ProductCard (Section 2.34)."""
    surface: str = Field(default="surface.secondary")
    border: str = Field(default="border.subtle")
    border_radius: str = Field(default="radius.md")
    aspect_ratio: str = Field(default="image.aspect.product")
    title_typography: str = Field(default="typography.body_m")
    price_typography: str = Field(default="typography.heading_s")
    merchant_typography: str = Field(default="typography.caption")
    padding: str = Field(default="space.component")
    hover_elevation: str = Field(default="elevation.2")
    focus_ring: str = Field(default="focus.ring")


class FashionCardComponentTokens(BaseContractModel):
    """Concrete token mapping for FashionCard editorial items."""
    surface: str = Field(default="surface.secondary")
    border: str = Field(default="border.default")
    border_radius: str = Field(default="radius.lg")
    aspect_ratio: str = Field(default="image.aspect.editorial")
    headline_typography: str = Field(default="typography.heading_m")
    caption_typography: str = Field(default="typography.body_s")
    padding: str = Field(default="space.component")
    hover_elevation: str = Field(default="elevation.3")


# ---------------------------------------------------------------------------
# 8. Theme Tokens & Full Registry
# ---------------------------------------------------------------------------

class ThemeTokens(BaseContractModel):
    """Resolved theme tokens for a specific mode (Light or Dark)."""
    mode: ThemeMode = Field(..., description="Theme mode (light or dark)")
    surfaces: SemanticSurfaces = Field(..., description="Semantic surfaces")
    content: SemanticContent = Field(..., description="Semantic text & icon content")
    borders: SemanticBorders = Field(..., description="Semantic borders")
    actions: SemanticActions = Field(..., description="Semantic action buttons")
    brand: BrandColorPalette = Field(..., description="Brand colors")
    status: StatusColorPalette = Field(..., description="Status colors")
    domains: DomainColorPalette = Field(..., description="Domain colors")
    focus: FocusTokens = Field(..., description="Focus indicator")


class DesignTokenRegistry(BaseContractModel):
    """Master production design token registry for FashXStudio (Phase 02)."""
    version: str = Field(default="1.0.0", description="Semantic token version")
    neutral_primitives: NeutralColorPrimitives = Field(default_factory=NeutralColorPrimitives)
    monk_skin_tones: MonkSkinTonePalette = Field(default_factory=MonkSkinTonePalette)
    brand_palette: BrandColorPalette = Field(default_factory=BrandColorPalette)
    status_palette: StatusColorPalette = Field(default_factory=StatusColorPalette)
    domain_palette: DomainColorPalette = Field(default_factory=DomainColorPalette)
    typography_families: TypographyFamilyTokens = Field(default_factory=TypographyFamilyTokens)
    font_weights: FontWeightTokens = Field(default_factory=FontWeightTokens)
    line_heights: LineHeightTokens = Field(default_factory=LineHeightTokens)
    typography_scale: TypographyScaleCatalog = Field(
        default_factory=lambda: TypographyScaleCatalog(
            display_xl=TypeScaleToken(size_px=48, line_height_px=56, letter_spacing_em=-0.02, weight=700),
            display_l=TypeScaleToken(size_px=40, line_height_px=48, letter_spacing_em=-0.02, weight=700),
            display_m=TypeScaleToken(size_px=32, line_height_px=40, letter_spacing_em=-0.015, weight=600),
            heading_xl=TypeScaleToken(size_px=28, line_height_px=36, letter_spacing_em=-0.01, weight=600),
            heading_l=TypeScaleToken(size_px=24, line_height_px=32, letter_spacing_em=-0.01, weight=600),
            heading_m=TypeScaleToken(size_px=20, line_height_px=28, letter_spacing_em=-0.005, weight=600),
            heading_s=TypeScaleToken(size_px=18, line_height_px=24, letter_spacing_em=0.0, weight=500),
            body_l=TypeScaleToken(size_px=17, line_height_px=26, letter_spacing_em=0.0, weight=400),
            body_m=TypeScaleToken(size_px=16, line_height_px=24, letter_spacing_em=0.0, weight=400),
            body_s=TypeScaleToken(size_px=14, line_height_px=20, letter_spacing_em=0.005, weight=400),
            label_l=TypeScaleToken(size_px=14, line_height_px=20, letter_spacing_em=0.01, weight=600),
            label_m=TypeScaleToken(size_px=12, line_height_px=16, letter_spacing_em=0.015, weight=500),
            label_s=TypeScaleToken(size_px=11, line_height_px=14, letter_spacing_em=0.02, weight=500),
            caption=TypeScaleToken(size_px=12, line_height_px=16, letter_spacing_em=0.01, weight=400),
            overline=TypeScaleToken(size_px=11, line_height_px=14, letter_spacing_em=0.05, weight=600),
        )
    )
    spacing_scale: SpacingScale = Field(default_factory=SpacingScale)
    semantic_spacing: SemanticSpacing = Field(default_factory=SemanticSpacing)
    sizing_scale: SizingScale = Field(default_factory=SizingScale)
    touch_targets: TargetSizeTokens = Field(default_factory=TargetSizeTokens)
    border_widths: BorderWidthTokens = Field(default_factory=BorderWidthTokens)
    radius_scale: RadiusScale = Field(default_factory=RadiusScale)
    elevations: ElevationTokens = Field(default_factory=ElevationTokens)
    opacities: OpacityTokens = Field(default_factory=OpacityTokens)
    z_indices: ZIndexTokens = Field(default_factory=ZIndexTokens)
    breakpoints: BreakpointPixels = Field(default_factory=BreakpointPixels)
    containers: ContainerMaxWidths = Field(default_factory=ContainerMaxWidths)
    grid: GridTokens = Field(default_factory=GridTokens)
    motion_durations: MotionDurationTokens = Field(default_factory=MotionDurationTokens)
    motion_easings: MotionEasingTokens = Field(default_factory=MotionEasingTokens)
    reduced_motion: ReducedMotionTokens = Field(default_factory=ReducedMotionTokens)
    focus: FocusTokens = Field(default_factory=FocusTokens)
    density_multipliers: DensityScaleMultipliers = Field(default_factory=DensityScaleMultipliers)
    product_card_tokens: ProductCardComponentTokens = Field(default_factory=ProductCardComponentTokens)
    fashion_card_tokens: FashionCardComponentTokens = Field(default_factory=FashionCardComponentTokens)


# ---------------------------------------------------------------------------
# 9. Token Validation Report Contract (Section 2.40)
# ---------------------------------------------------------------------------

class TokenContrastCheck(BaseContractModel):
    """WCAG 2.2 contrast evaluation result."""
    foreground_token: str
    background_token: str
    foreground_hex: str
    background_hex: str
    contrast_ratio: float
    passes_aa: bool
    passes_aaa: bool
    context: str


class TokenValidationReport(BaseContractModel):
    """Validation report for token consistency, dangling references, and WCAG contrast."""
    is_valid: bool
    total_tokens_checked: int
    contrast_checks: list[TokenContrastCheck]
    broken_references: list[str] = Field(default_factory=list)
    accessibility_status: str = Field(default="WCAG 2.2 AAA Compliant")
