"""Unit tests for FashXStudio Design Token System (Phase 02).

Validates token primitives, Monk Skin Tone (MST) scale, typography hierarchy,
4px spacing increments, z-index layering, touch target compliance, WCAG 2.2 contrast ratios,
and theme resolution under Constitution Rule I02 (Contract Primacy).
"""

import pytest
from fashx.visual.tokens_service import (
    calculate_adaptive_columns,
    calculate_contrast_ratio,
    get_theme_tokens,
    get_token_registry,
    hex_to_rgb,
    relative_luminance,
    validate_tokens,
)
from schemas.visual.tokens import (
    DensityMode,
    DesignTokenRegistry,
    ThemeMode,
    ThemeTokens,
    TokenValidationReport,
)


def test_token_registry_primitives() -> None:
    """Verify registry singleton and baseline primitive values."""
    registry = get_token_registry()
    assert isinstance(registry, DesignTokenRegistry)
    assert registry.version == "1.0.0"
    assert registry.neutral_primitives.neutral_0 == "#FFFFFF"
    assert registry.neutral_primitives.neutral_950 == "#030712"
    assert registry.brand_palette.primary == "#0F172A"
    assert registry.brand_palette.secondary == "#6366F1"


def test_monk_skin_tone_palette() -> None:
    """Verify Monk Skin Tone 10-point scale and undertone calibration."""
    registry = get_token_registry()
    mst = registry.monk_skin_tones
    tones = [
        mst.mst_01, mst.mst_02, mst.mst_03, mst.mst_04, mst.mst_05,
        mst.mst_06, mst.mst_07, mst.mst_08, mst.mst_09, mst.mst_10,
    ]
    assert len(tones) == 10
    # Every tone is a valid 7-character hex code
    for tone in tones:
        assert tone.startswith("#")
        assert len(tone) == 7
    # Undertones are populated
    assert mst.undertone_warm.startswith("#")
    assert mst.undertone_cool.startswith("#")
    assert mst.undertone_neutral.startswith("#")


def test_typography_scale() -> None:
    """Verify 15 typography levels, sizes, and line heights."""
    registry = get_token_registry()
    scale = registry.typography_scale
    assert scale.display_xl.size_px == 48
    assert scale.display_xl.line_height_px == 56
    assert scale.display_l.size_px == 40
    assert scale.display_m.size_px == 32
    assert scale.heading_xl.size_px == 28
    assert scale.heading_l.size_px == 24
    assert scale.heading_m.size_px == 20
    assert scale.heading_s.size_px == 18
    assert scale.body_l.size_px == 17
    assert scale.body_m.size_px == 16
    assert scale.body_s.size_px == 14
    assert scale.label_l.size_px == 14
    assert scale.label_m.size_px == 12
    assert scale.label_s.size_px == 11
    assert scale.caption.size_px == 12
    assert scale.overline.size_px == 11


def test_spacing_scale_4px_base() -> None:
    """Verify 4px base increment spacing scale."""
    registry = get_token_registry()
    spacing = registry.spacing_scale
    tokens = [
        spacing.space_1, spacing.space_2, spacing.space_3, spacing.space_4,
        spacing.space_5, spacing.space_6, spacing.space_8, spacing.space_10,
        spacing.space_12, spacing.space_16, spacing.space_20, spacing.space_24,
    ]
    for val in tokens:
        assert val % 4 == 0, f"Spacing {val} is not a multiple of 4px"
    assert spacing.space_1 == 4
    assert spacing.space_24 == 96


def test_semantic_spacing_hierarchy() -> None:
    """Verify semantic spacing hierarchy strictly increases."""
    registry = get_token_registry()
    sem = registry.semantic_spacing
    assert sem.inline < sem.element < sem.component < sem.section < sem.page


def test_z_index_hierarchy() -> None:
    """Verify strict z-index layering to avoid arbitrary z-index: 9999."""
    registry = get_token_registry()
    z = registry.z_indices
    assert z.base < z.sticky < z.dropdown < z.overlay < z.modal < z.popover < z.toast < z.max
    assert z.max == 9999


def test_touch_target_accessibility() -> None:
    """Verify touch target minimums adhere to WCAG 2.5.5 / 2.5.8."""
    registry = get_token_registry()
    targets = registry.touch_targets
    assert targets.compact_desktop_min_px >= 36
    assert targets.primary_control_min_px >= 40
    assert targets.touch_target_min_px >= 44


def test_light_and_dark_theme_resolution() -> None:
    """Verify light and dark theme resolutions and color role mappings."""
    light = get_theme_tokens(ThemeMode.LIGHT)
    dark = get_theme_tokens(ThemeMode.DARK)

    assert light.mode == ThemeMode.LIGHT
    assert dark.mode == ThemeMode.DARK

    # Surfaces
    assert light.surfaces.primary == "#FFFFFF"
    assert dark.surfaces.primary == "#030712"
    assert light.surfaces.secondary == "#F9FAFB"
    assert dark.surfaces.secondary == "#111827"

    # Content
    assert light.content.primary == "#111827"
    assert dark.content.primary == "#F9FAFB"

    # Actions
    assert light.actions.primary == "#111827"
    assert light.actions.primary_text == "#FFFFFF"
    assert dark.actions.primary == "#F9FAFB"
    assert dark.actions.primary_text == "#030712"


def test_wcag_contrast_calculation() -> None:
    """Verify relative luminance and WCAG contrast ratio calculations."""
    # Absolute black on absolute white
    ratio_max = calculate_contrast_ratio("#000000", "#FFFFFF")
    assert ratio_max == 21.0

    # Same colors
    ratio_min = calculate_contrast_ratio("#FFFFFF", "#FFFFFF")
    assert ratio_min == 1.0

    # Light theme primary content on surface
    light = get_theme_tokens(ThemeMode.LIGHT)
    light_contrast = calculate_contrast_ratio(light.content.primary, light.surfaces.primary)
    assert light_contrast >= 7.0, f"Light theme contrast {light_contrast} below AAA"

    # Dark theme primary content on surface
    dark = get_theme_tokens(ThemeMode.DARK)
    dark_contrast = calculate_contrast_ratio(dark.content.primary, dark.surfaces.primary)
    assert dark_contrast >= 7.0, f"Dark theme contrast {dark_contrast} below AAA"


def test_adaptive_grid_calculation() -> None:
    """Verify adaptive column calculation across responsive container widths."""
    # Mobile (360px)
    cols_mobile = calculate_adaptive_columns(360, min_card_width_px=240, gutter_px=16)
    assert cols_mobile == 1

    # Tablet (768px)
    cols_tablet = calculate_adaptive_columns(768, min_card_width_px=240, gutter_px=16)
    assert cols_tablet == 3

    # Desktop (1280px)
    cols_desktop = calculate_adaptive_columns(1280, min_card_width_px=240, gutter_px=16)
    assert cols_desktop == 5

    # Boundary: width 0 returns 1 column
    assert calculate_adaptive_columns(0) == 1


def test_token_validation_report() -> None:
    """Verify automated token validation produces a valid report with zero broken references."""
    report = validate_tokens()
    assert isinstance(report, TokenValidationReport)
    assert report.is_valid is True
    assert len(report.broken_references) == 0
    assert len(report.contrast_checks) >= 6
    assert "Compliant" in report.accessibility_status
