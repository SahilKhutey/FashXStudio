from typing import Any


def to_css_variables(tokens: dict[str, Any]) -> dict[str, str]:
    color = tokens.get("color", {})
    brand = color.get("brand", {})
    surface = color.get("surface", {})
    text = color.get("text", {})
    border = color.get("border", {})

    typography = tokens.get("typography", {})
    font_family = typography.get("fontFamily", {})
    font_size = typography.get("fontSize", {})
    font_weight = typography.get("fontWeight", {})

    spacing = tokens.get("spacing", {})
    radius = tokens.get("radius", {})
    shadow = tokens.get("shadow", {})
    accessibility = tokens.get("accessibility", {})

    return {
        # Colors
        "--mm-color-brand-primary": str(brand.get("primary", "#18181b")),
        "--mm-color-brand-secondary": str(brand.get("secondary", brand.get("primary", "#71717a"))),
        "--mm-color-brand-accent": str(brand.get("accent", brand.get("primary", "#2563eb"))),
        "--mm-color-surface-default": str(surface.get("default", "#ffffff")),
        "--mm-color-surface-subtle": str(surface.get("subtle", surface.get("default", "#f4f4f5"))),
        "--mm-color-surface-raised": str(surface.get("raised", surface.get("default", "#ffffff"))),
        "--mm-color-text-primary": str(text.get("primary", "#09090b")),
        "--mm-color-text-secondary": str(text.get("secondary", text.get("primary", "#71717a"))),
        "--mm-color-text-inverse": str(text.get("inverse", "#ffffff")),
        "--mm-color-border-default": str(border.get("default", "#e4e4e7")),
        # Typography
        "--mm-font-family-body": str(font_family.get("body", "Inter")),
        "--mm-font-family-heading": str(font_family.get("heading", "Inter")),
        "--mm-font-size-small": str(font_size.get("small", "0.875rem")),
        "--mm-font-size-body": str(font_size.get("body", "1rem")),
        "--mm-font-size-heading": str(font_size.get("heading", "1.5rem")),
        "--mm-font-size-display": str(font_size.get("display", "2rem")),
        "--mm-font-weight-normal": str(font_weight.get("normal", 400)),
        "--mm-font-weight-medium": str(font_weight.get("medium", 500)),
        "--mm-font-weight-bold": str(font_weight.get("bold", 700)),
        # Spacing
        "--mm-spacing-xs": str(spacing.get("xs", "0.25rem")),
        "--mm-spacing-sm": str(spacing.get("sm", "0.5rem")),
        "--mm-spacing-md": str(spacing.get("md", "1rem")),
        "--mm-spacing-lg": str(spacing.get("lg", "1.5rem")),
        "--mm-spacing-xl": str(spacing.get("xl", "2rem")),
        # Radius
        "--mm-radius-small": str(radius.get("small", "0.25rem")),
        "--mm-radius-medium": str(radius.get("medium", "0.5rem")),
        "--mm-radius-large": str(radius.get("large", "0.75rem")),
        # Shadow
        "--mm-shadow-card": str(shadow.get("card", "0 1px 3px rgba(0,0,0,0.05)")),
        # Accessibility
        "--mm-focus-ring-color": str(accessibility.get("focusRingColor", brand.get("primary", "#2563eb"))),
        "--mm-focus-ring-width": str(accessibility.get("focusRingWidth", "2px")),
        "--mm-min-touch-target": str(accessibility.get("minTouchTarget", "44px")),
    }
