"""Component Framework Service — Phase 05.

Provides the canonical component catalog, component specifications, token mappings,
and prop validation for Level 1 (Primitives) and Level 2 (Core UI) components.
Adheres to Rule I01 (Layer Separation) and Rule I02 (Contract Primacy).
"""

from typing import Any
from schemas.visual.components import (
    BadgeSpecContract,
    ButtonSpecContract,
    ButtonVariant,
    CardSpecContract,
    CardVariant,
    ComponentCatalogContract,
    ComponentDefinitionContract,
    ComponentSize,
    ComponentTaxonomy,
    ComponentValidationReportContract,
    FormFieldSpecContract,
    InputSpecContract,
    ModalSpecContract,
    RatingSpecContract,
    SegmentedControlSpecContract,
    SkeletonShape,
    SkeletonSpecContract,
    TypographyRole,
    TypographySpecContract,
)


# ---------------------------------------------------------------------------
# Canonical Component Catalog
# ---------------------------------------------------------------------------

PRIMITIVE_COMPONENTS: list[ComponentDefinitionContract] = [
    ComponentDefinitionContract(
        name="Button",
        taxonomy=ComponentTaxonomy.LEVEL_1_PRIMITIVE,
        description="Core interactive trigger with 5 variants, 3 sizes, loading and disabled states.",
        available_variants=["primary", "secondary", "outline", "ghost", "destructive"],
        available_sizes=["sm", "md", "lg"],
        design_tokens_used=[
            "action.primary", "action.primary_text", "action.secondary",
            "action.hover", "radius.sm", "radius.md", "space.4",
            "focus.ring_color", "target.min_touch",
        ],
        wcag_criteria=["WCAG 2.2 2.5.8 (Target Size >= 44px)", "WCAG 2.2 1.4.3 (Contrast >= 4.5:1)", "WCAG 2.2 2.4.7 (Focus Visible)"],
        has_interactive_states=True,
    ),
    ComponentDefinitionContract(
        name="Input",
        taxonomy=ComponentTaxonomy.LEVEL_1_PRIMITIVE,
        description="Configurable single-line text input with label, icons, clear button, and error state.",
        available_variants=["text", "search", "email", "password", "number", "phone"],
        available_sizes=["sm", "md", "lg"],
        design_tokens_used=[
            "surface.primary", "surface.secondary", "border.default",
            "border.focus", "border.error", "content.primary",
            "content.tertiary", "radius.sm", "space.3",
        ],
        wcag_criteria=["WCAG 2.2 3.3.1 (Error Identification)", "WCAG 2.2 3.3.2 (Labels or Instructions)", "WCAG 2.2 2.4.7 (Focus Visible)"],
        has_interactive_states=True,
    ),
    ComponentDefinitionContract(
        name="Typography",
        taxonomy=ComponentTaxonomy.LEVEL_1_PRIMITIVE,
        description="Unified typography component supporting 15 type scale roles with token-mapped colors.",
        available_variants=[r.value for r in TypographyRole],
        available_sizes=["sm", "md", "lg"],
        design_tokens_used=[
            "font.family.primary", "font.family.display", "type.scale.*",
            "content.primary", "content.secondary", "content.tertiary",
        ],
        wcag_criteria=["WCAG 2.2 1.4.3 (Contrast Minimum)", "WCAG 2.2 1.4.6 (Contrast Enhanced)"],
        has_interactive_states=False,
    ),
    ComponentDefinitionContract(
        name="Badge",
        taxonomy=ComponentTaxonomy.LEVEL_1_PRIMITIVE,
        description="Status indicator, tag, or pill chip with 8 visual variants and dismiss support.",
        available_variants=["default", "brand", "success", "warning", "error", "accent", "neutral", "outline"],
        available_sizes=["sm", "md"],
        design_tokens_used=[
            "status.success", "status.warning", "status.error", "status.info",
            "brand.primary", "brand.accent", "radius.full", "space.1", "space.2",
        ],
        wcag_criteria=["WCAG 2.2 1.4.1 (Use of Color)", "WCAG 2.2 1.4.3 (Contrast Minimum)"],
        has_interactive_states=True,
    ),
    ComponentDefinitionContract(
        name="Skeleton",
        taxonomy=ComponentTaxonomy.LEVEL_1_PRIMITIVE,
        description="Structural pulse loading placeholder with rectangle, circle, and text shapes.",
        available_variants=["rectangle", "rounded", "circle", "text"],
        available_sizes=["sm", "md", "lg"],
        design_tokens_used=["neutral.200", "neutral.300", "motion.duration.normal", "radius.sm"],
        wcag_criteria=["WCAG 2.2 2.2.2 (Pause, Stop, Hide)", "WCAG 2.2 2.3.3 (Animation from Interactions)"],
        has_interactive_states=False,
    ),
    ComponentDefinitionContract(
        name="Divider",
        taxonomy=ComponentTaxonomy.LEVEL_1_PRIMITIVE,
        description="Horizontal or vertical content separator with subtle, strong, and labeled variants.",
        available_variants=["horizontal", "vertical", "subtle", "strong", "labeled"],
        available_sizes=["sm", "md"],
        design_tokens_used=["border.subtle", "border.strong", "space.4"],
        wcag_criteria=["WCAG 2.2 1.4.11 (Non-text Contrast)"],
        has_interactive_states=False,
    ),
    ComponentDefinitionContract(
        name="Spinner",
        taxonomy=ComponentTaxonomy.LEVEL_1_PRIMITIVE,
        description="Circular indeterminate activity spinner with semantic brand and neutral coloring.",
        available_variants=["brand", "neutral", "white"],
        available_sizes=["sm", "md", "lg"],
        design_tokens_used=["brand.primary", "neutral.400", "neutral.0"],
        wcag_criteria=["WCAG 2.2 4.1.3 (Status Messages)"],
        has_interactive_states=False,
    ),
]

CORE_UI_COMPONENTS: list[ComponentDefinitionContract] = [
    ComponentDefinitionContract(
        name="Card",
        taxonomy=ComponentTaxonomy.LEVEL_2_CORE_UI,
        description="Surface container with 3 variants, 0-5 elevations, responsive gutters, and hover lift.",
        available_variants=["elevated", "outlined", "filled"],
        available_sizes=["sm", "md", "lg"],
        design_tokens_used=[
            "surface.primary", "surface.secondary", "border.subtle",
            "elevation.1", "elevation.2", "elevation.3", "radius.md", "space.4",
        ],
        wcag_criteria=["WCAG 2.2 1.4.11 (Non-text Contrast)", "WCAG 2.2 2.4.7 (Focus Visible)"],
        has_interactive_states=True,
    ),
    ComponentDefinitionContract(
        name="Modal",
        taxonomy=ComponentTaxonomy.LEVEL_2_CORE_UI,
        description="Accessible modal dialog with backdrop scrim, focus trapping, Escape dismissal, and action slots.",
        available_variants=["standard", "alert", "confirmation", "fullscreen"],
        available_sizes=["sm", "md", "lg"],
        design_tokens_used=[
            "surface.primary", "opacity.scrim", "z_index.modal",
            "radius.lg", "elevation.5", "space.6",
        ],
        wcag_criteria=["WCAG 2.2 2.1.2 (No Keyboard Trap)", "WCAG 2.2 2.4.3 (Focus Order)", "WCAG 2.2 4.1.2 (Name, Role, Value)"],
        has_interactive_states=True,
    ),
    ComponentDefinitionContract(
        name="Rating",
        taxonomy=ComponentTaxonomy.LEVEL_2_CORE_UI,
        description="Star rating with half-star increments, fit score indicators, and review counts.",
        available_variants=["stars", "fit_bias", "numeric"],
        available_sizes=["sm", "md", "lg"],
        design_tokens_used=["brand.accent", "status.warning", "neutral.300", "type.scale.caption"],
        wcag_criteria=["WCAG 2.2 1.1.1 (Non-text Content)", "WCAG 2.2 1.4.3 (Contrast Minimum)"],
        has_interactive_states=True,
    ),
    ComponentDefinitionContract(
        name="SegmentedControl",
        taxonomy=ComponentTaxonomy.LEVEL_2_CORE_UI,
        description="Inline toggle selector with animated sliding pill indicator and accessible tablist role.",
        available_variants=["default", "pill", "compact"],
        available_sizes=["sm", "md"],
        design_tokens_used=[
            "surface.secondary", "surface.primary", "action.primary",
            "content.primary", "radius.md", "motion.duration.fast",
        ],
        wcag_criteria=["WCAG 2.2 2.1.1 (Keyboard)", "WCAG 2.2 4.1.2 (Name, Role, Value)"],
        has_interactive_states=True,
    ),
    ComponentDefinitionContract(
        name="FormField",
        taxonomy=ComponentTaxonomy.LEVEL_2_CORE_UI,
        description="Composite form layout linking label, input slot, required indicator, and error live regions.",
        available_variants=["default", "inline", "floating"],
        available_sizes=["md"],
        design_tokens_used=[
            "content.primary", "status.error", "space.1", "space.2", "space.4",
        ],
        wcag_criteria=["WCAG 2.2 3.3.1 (Error Identification)", "WCAG 2.2 3.3.2 (Labels or Instructions)"],
        has_interactive_states=False,
    ),
    ComponentDefinitionContract(
        name="Accordion",
        taxonomy=ComponentTaxonomy.LEVEL_2_CORE_UI,
        description="Collapsible disclosure panel with animated chevron and accessible expand/collapse state.",
        available_variants=["default", "bordered", "flush"],
        available_sizes=["md", "lg"],
        design_tokens_used=[
            "border.subtle", "content.primary", "motion.duration.normal", "space.4",
        ],
        wcag_criteria=["WCAG 2.2 2.1.1 (Keyboard)", "WCAG 2.2 4.1.2 (Name, Role, Value)"],
        has_interactive_states=True,
    ),
]

_CANONICAL_CATALOG = ComponentCatalogContract(
    primitives=PRIMITIVE_COMPONENTS,
    core_ui=CORE_UI_COMPONENTS,
)


def get_component_catalog() -> ComponentCatalogContract:
    """Return the complete canonical component catalog."""
    return _CANONICAL_CATALOG


def get_component_definition(name: str) -> ComponentDefinitionContract | None:
    """Find a component definition by name."""
    return _CANONICAL_CATALOG.find_component(name)


# ---------------------------------------------------------------------------
# Prop Validation Engine
# ---------------------------------------------------------------------------

def validate_component_props(
    component_name: str,
    props: dict[str, Any],
) -> ComponentValidationReportContract:
    """Validate runtime props against the component's strict contract."""
    spec_map = {
        "button": ButtonSpecContract,
        "input": InputSpecContract,
        "badge": BadgeSpecContract,
        "typography": TypographySpecContract,
        "skeleton": SkeletonSpecContract,
        "card": CardSpecContract,
        "modal": ModalSpecContract,
        "rating": RatingSpecContract,
        "segmentedcontrol": SegmentedControlSpecContract,
        "formfield": FormFieldSpecContract,
    }

    schema_cls = spec_map.get(component_name.lower())
    if not schema_cls:
        return ComponentValidationReportContract(
            is_valid=False,
            component_name=component_name,
            errors=[f"Component '{component_name}' is not recognized in the component catalog."],
            validated_props={},
        )

    try:
        validated = schema_cls(**props)
        return ComponentValidationReportContract(
            is_valid=True,
            component_name=component_name,
            errors=[],
            validated_props=validated.model_dump(),
        )
    except Exception as exc:
        return ComponentValidationReportContract(
            is_valid=False,
            component_name=component_name,
            errors=[str(exc)],
            validated_props={},
        )
