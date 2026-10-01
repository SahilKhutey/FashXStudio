"""Component Framework Service — Phase 05.

Provides the canonical component catalog, component specifications, token mappings,
and prop validation for Level 1 (Primitives), Level 2 (Core UI), and Level 3 (Composites).
Adheres to Rule I01 (Layer Separation) and Rule I02 (Contract Primacy).
"""

from typing import Any
from schemas.visual.components import (
    ActionBarSpecContract,
    AlertSpecContract,
    AvatarSpecContract,
    BadgeSpecContract,
    BoxSpecContract,
    ButtonSpecContract,
    CardSpecContract,
    ChipSpecContract,
    CollectionCardSpecContract,
    ComponentCatalogContract,
    ComponentDefinitionContract,
    ComponentTaxonomy,
    ComponentValidationReportContract,
    ContainerSpecContract,
    DialogConfirmSpecContract,
    DrawerSpecContract,
    EmptyStateSpecContract,
    ErrorStateSpecContract,
    FashionCardSpecContract,
    FilterBarSpecContract,
    FormFieldSpecContract,
    GridSpecContract,
    IconButtonSpecContract,
    InlineSpecContract,
    InputSpecContract,
    LinkSpecContract,
    LookCardSpecContract,
    ModalSpecContract,
    PaginationSpecContract,
    PriceSpecContract,
    ProductCardSpecContract,
    ProgressSpecContract,
    QuantityControlSpecContract,
    RatingSpecContract,
    RecommendationCardSpecContract,
    SearchBarSpecContract,
    SegmentedControlSpecContract,
    SkeletonSpecContract,
    StackSpecContract,
    TypographySpecContract,
)


# ---------------------------------------------------------------------------
# Canonical Component Catalog (Sections 5.2 - 5.55)
# ---------------------------------------------------------------------------

PRIMITIVE_COMPONENTS: list[ComponentDefinitionContract] = [
    ComponentDefinitionContract(
        name="Box",
        taxonomy=ComponentTaxonomy.LEVEL_1_PRIMITIVE,
        description="Controlled layout/styling primitive consuming tokens for padding, margin, surface, and border.",
        available_variants=["default"],
        available_sizes=["sm", "md", "lg"],
        design_tokens_used=["surface.*", "space.*", "radius.*", "border.*"],
        wcag_criteria=["WCAG 2.2 1.4.11 (Non-text Contrast)"],
        has_interactive_states=False,
    ),
    ComponentDefinitionContract(
        name="Stack",
        taxonomy=ComponentTaxonomy.LEVEL_1_PRIMITIVE,
        description="Vertical layout primitive with token-based gaps for forms, cards, and page sections.",
        available_variants=["vertical"],
        available_sizes=["sm", "md", "lg"],
        design_tokens_used=["space.component.md", "space.component.lg"],
        wcag_criteria=["WCAG 2.2 1.3.2 (Meaningful Sequence)"],
        has_interactive_states=False,
    ),
    ComponentDefinitionContract(
        name="Inline",
        taxonomy=ComponentTaxonomy.LEVEL_1_PRIMITIVE,
        description="Horizontal layout primitive with gap, wrapping, and justification support for actions and tags.",
        available_variants=["horizontal"],
        available_sizes=["sm", "md", "lg"],
        design_tokens_used=["space.2", "space.3", "space.4"],
        wcag_criteria=["WCAG 2.2 1.3.2 (Meaningful Sequence)"],
        has_interactive_states=False,
    ),
    ComponentDefinitionContract(
        name="Grid",
        taxonomy=ComponentTaxonomy.LEVEL_1_PRIMITIVE,
        description="Responsive multi-column composition primitive integrating with Phase 2 grid tokens.",
        available_variants=["fluid", "fixed"],
        available_sizes=["sm", "md", "lg"],
        design_tokens_used=["grid.columns.*", "grid.gutter.*"],
        wcag_criteria=["WCAG 2.2 1.4.10 (Reflow)"],
        has_interactive_states=False,
    ),
    ComponentDefinitionContract(
        name="Container",
        taxonomy=ComponentTaxonomy.LEVEL_1_PRIMITIVE,
        description="Content container establishing max width, responsive gutters, and centering.",
        available_variants=["centered", "fluid"],
        available_sizes=["sm", "md", "lg", "xl"],
        design_tokens_used=["container.max_width.*", "space.component"],
        wcag_criteria=["WCAG 2.2 1.4.10 (Reflow)"],
        has_interactive_states=False,
    ),
    ComponentDefinitionContract(
        name="Button",
        taxonomy=ComponentTaxonomy.LEVEL_1_PRIMITIVE,
        description="Core interactive trigger with 6 variants, 3 sizes, loading and disabled states.",
        available_variants=["primary", "secondary", "tertiary", "outline", "ghost", "destructive"],
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
        name="IconButton",
        taxonomy=ComponentTaxonomy.LEVEL_1_PRIMITIVE,
        description="Compact icon-only button with mandatory accessible name and >= 44px touch target.",
        available_variants=["ghost", "primary", "secondary", "outline"],
        available_sizes=["sm", "md", "lg"],
        design_tokens_used=["action.primary", "radius.full", "target.min_touch"],
        wcag_criteria=["WCAG 2.2 4.1.2 (Name, Role, Value)", "WCAG 2.2 2.5.8 (Target Size >= 44px)"],
        has_interactive_states=True,
    ),
    ComponentDefinitionContract(
        name="Link",
        taxonomy=ComponentTaxonomy.LEVEL_1_PRIMITIVE,
        description="Accessible navigation link supporting internal routing and external destinations.",
        available_variants=["default", "subtle", "underline"],
        available_sizes=["sm", "md", "lg"],
        design_tokens_used=["content.primary", "brand.secondary", "focus.ring_color"],
        wcag_criteria=["WCAG 2.2 2.4.4 (Link Purpose)", "WCAG 2.2 2.4.7 (Focus Visible)"],
        has_interactive_states=True,
    ),
    ComponentDefinitionContract(
        name="Input",
        taxonomy=ComponentTaxonomy.LEVEL_1_PRIMITIVE,
        description="Configurable single-line text input with label, icons, clear button, and error state.",
        available_variants=["text", "search", "email", "password", "number", "phone", "textarea"],
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
        available_variants=[
            "display_xl", "display_l", "display_m", "heading_xl", "heading_l",
            "heading_m", "heading_s", "heading_xs", "body_l", "body_m", "body_s",
            "label_l", "label_m", "label_s", "caption", "overline"
        ],
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
        available_variants=["default", "brand", "success", "warning", "error", "accent", "neutral", "outline", "info"],
        available_sizes=["sm", "md"],
        design_tokens_used=[
            "status.success", "status.warning", "status.error", "status.info",
            "brand.primary", "brand.accent", "radius.full", "space.1", "space.2",
        ],
        wcag_criteria=["WCAG 2.2 1.4.1 (Use of Color)", "WCAG 2.2 1.4.3 (Contrast Minimum)"],
        has_interactive_states=True,
    ),
    ComponentDefinitionContract(
        name="Chip",
        taxonomy=ComponentTaxonomy.LEVEL_1_PRIMITIVE,
        description="Selectable or removable attribute chip for filter facets and metadata.",
        available_variants=["filter", "attribute", "selectable"],
        available_sizes=["sm", "md"],
        design_tokens_used=["surface.secondary", "radius.full", "action.primary"],
        wcag_criteria=["WCAG 2.2 4.1.2 (Name, Role, Value)"],
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
]

CORE_UI_COMPONENTS: list[ComponentDefinitionContract] = [
    ComponentDefinitionContract(
        name="Card",
        taxonomy=ComponentTaxonomy.LEVEL_2_CORE_UI,
        description="Surface container with 7 variants, 0-5 elevations, responsive gutters, and hover lift.",
        available_variants=["default", "elevated", "outlined", "filled", "interactive", "compact", "media"],
        available_sizes=["sm", "md", "lg"],
        design_tokens_used=[
            "surface.primary", "surface.secondary", "border.subtle",
            "elevation.1", "elevation.2", "elevation.3", "radius.md", "space.4",
        ],
        wcag_criteria=["WCAG 2.2 1.4.11 (Non-text Contrast)", "WCAG 2.2 2.4.7 (Focus Visible)"],
        has_interactive_states=True,
    ),
    ComponentDefinitionContract(
        name="Avatar",
        taxonomy=ComponentTaxonomy.LEVEL_2_CORE_UI,
        description="User, creator, brand account visual identifier with image, initials, and fallback states.",
        available_variants=["circle", "rounded"],
        available_sizes=["sm", "md", "lg"],
        design_tokens_used=["radius.full", "surface.tertiary", "content.primary"],
        wcag_criteria=["WCAG 2.2 1.1.1 (Non-text Content)"],
        has_interactive_states=False,
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
        name="Drawer",
        taxonomy=ComponentTaxonomy.LEVEL_2_CORE_UI,
        description="Slide-out drawer panel for filters, navigation, and settings.",
        available_variants=["left", "right", "bottom"],
        available_sizes=["md", "lg"],
        design_tokens_used=["surface.primary", "z_index.modal", "elevation.4"],
        wcag_criteria=["WCAG 2.2 2.1.2 (No Keyboard Trap)", "WCAG 2.2 4.1.2 (Name, Role, Value)"],
        has_interactive_states=True,
    ),
    ComponentDefinitionContract(
        name="DialogConfirm",
        taxonomy=ComponentTaxonomy.LEVEL_2_CORE_UI,
        description="Consequential confirmation dialog with explicit confirm/cancel buttons.",
        available_variants=["default", "destructive"],
        available_sizes=["sm", "md"],
        design_tokens_used=["surface.primary", "action.destructive", "radius.md"],
        wcag_criteria=["WCAG 2.2 3.3.4 (Error Prevention - Legal, Financial, Data)"],
        has_interactive_states=True,
    ),
    ComponentDefinitionContract(
        name="Alert",
        taxonomy=ComponentTaxonomy.LEVEL_2_CORE_UI,
        description="Persistent inline notification with info, warning, error, and success severities.",
        available_variants=["info", "success", "warning", "error"],
        available_sizes=["md"],
        design_tokens_used=["status.error", "status.warning", "status.success", "status.info"],
        wcag_criteria=["WCAG 2.2 4.1.3 (Status Messages)"],
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
        name="Price",
        taxonomy=ComponentTaxonomy.LEVEL_2_CORE_UI,
        description="Standardized price display with current, strikethrough original, and discount percentage.",
        available_variants=["standard", "discounted", "compact"],
        available_sizes=["sm", "md", "lg"],
        design_tokens_used=["content.primary", "content.tertiary", "status.success", "type.scale.headingS"],
        wcag_criteria=["WCAG 2.2 1.4.3 (Contrast Minimum)"],
        has_interactive_states=False,
    ),
    ComponentDefinitionContract(
        name="QuantityControl",
        taxonomy=ComponentTaxonomy.LEVEL_2_CORE_UI,
        description="Stepper control for item count with minimum, maximum, and validation boundaries.",
        available_variants=["standard", "compact"],
        available_sizes=["sm", "md"],
        design_tokens_used=["border.default", "target.min_touch", "type.scale.bodyM"],
        wcag_criteria=["WCAG 2.2 2.5.8 (Target Size >= 44px)"],
        has_interactive_states=True,
    ),
    ComponentDefinitionContract(
        name="Pagination",
        taxonomy=ComponentTaxonomy.LEVEL_2_CORE_UI,
        description="Accessible page number pagination with previous/next triggers.",
        available_variants=["numbered", "compact"],
        available_sizes=["md"],
        design_tokens_used=["action.primary", "surface.secondary", "target.min_touch"],
        wcag_criteria=["WCAG 2.2 2.4.4 (Link Purpose)", "WCAG 2.2 2.5.8 (Target Size >= 44px)"],
        has_interactive_states=True,
    ),
    ComponentDefinitionContract(
        name="Progress",
        taxonomy=ComponentTaxonomy.LEVEL_2_CORE_UI,
        description="Progress bar and circular indicators for onboarding, checkout, and AI processing.",
        available_variants=["linear", "circular", "stepper"],
        available_sizes=["sm", "md"],
        design_tokens_used=["brand.primary", "surface.secondary"],
        wcag_criteria=["WCAG 2.2 4.1.3 (Status Messages)"],
        has_interactive_states=False,
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
        name="EmptyState",
        taxonomy=ComponentTaxonomy.LEVEL_2_CORE_UI,
        description="Accessible empty state view explaining what is empty, why it matters, and next steps.",
        available_variants=["default", "compact"],
        available_sizes=["md", "lg"],
        design_tokens_used=["content.primary", "content.secondary", "action.primary"],
        wcag_criteria=["WCAG 2.2 3.3.2 (Labels or Instructions)"],
        has_interactive_states=True,
    ),
    ComponentDefinitionContract(
        name="ErrorState",
        taxonomy=ComponentTaxonomy.LEVEL_2_CORE_UI,
        description="Standardized error view with actionable retry and recovery navigation destinations.",
        available_variants=["default", "card"],
        available_sizes=["md", "lg"],
        design_tokens_used=["status.error", "action.primary", "surface.primary"],
        wcag_criteria=["WCAG 2.2 3.3.1 (Error Identification)"],
        has_interactive_states=True,
    ),
]

COMPOSITE_COMPONENTS: list[ComponentDefinitionContract] = [
    ComponentDefinitionContract(
        name="ProductCard",
        taxonomy=ComponentTaxonomy.LEVEL_3_COMPOSITE,
        description="First major commerce composite integrating media, brand, title, price, rating, and wishlist trigger.",
        available_variants=["standard", "horizontal", "compact"],
        available_sizes=["md", "lg"],
        design_tokens_used=["surface.primary", "elevation.1", "radius.md", "space.3"],
        wcag_criteria=["WCAG 2.2 1.1.1 (Non-text Content)", "WCAG 2.2 2.5.8 (Target Size >= 44px)"],
        has_interactive_states=True,
    ),
    ComponentDefinitionContract(
        name="FashionCard",
        taxonomy=ComponentTaxonomy.LEVEL_3_COMPOSITE,
        description="Editorial content card emphasizing visual story, title, category, and narrative description.",
        available_variants=["hero", "grid", "magazine"],
        available_sizes=["md", "lg"],
        design_tokens_used=["font.family.display", "surface.primary", "radius.lg"],
        wcag_criteria=["WCAG 2.2 1.4.3 (Contrast Minimum)"],
        has_interactive_states=True,
    ),
    ComponentDefinitionContract(
        name="LookCard",
        taxonomy=ComponentTaxonomy.LEVEL_3_COMPOSITE,
        description="Curated outfit look card displaying styling imagery, item count, and save action.",
        available_variants=["default", "carousel"],
        available_sizes=["md", "lg"],
        design_tokens_used=["surface.primary", "radius.md", "action.primary"],
        wcag_criteria=["WCAG 2.2 2.5.8 (Target Size >= 44px)"],
        has_interactive_states=True,
    ),
    ComponentDefinitionContract(
        name="CollectionCard",
        taxonomy=ComponentTaxonomy.LEVEL_3_COMPOSITE,
        description="Seasonal/thematic collection display with product tally and exploration CTA.",
        available_variants=["hero", "card"],
        available_sizes=["lg"],
        design_tokens_used=["surface.primary", "radius.lg", "brand.primary"],
        wcag_criteria=["WCAG 2.2 1.4.3 (Contrast Minimum)"],
        has_interactive_states=True,
    ),
    ComponentDefinitionContract(
        name="RecommendationCard",
        taxonomy=ComponentTaxonomy.LEVEL_3_COMPOSITE,
        description="AI-generated outfit/product suggestion with explicit explainability reason badge.",
        available_variants=["standard", "detailed"],
        available_sizes=["md", "lg"],
        design_tokens_used=["surface.primary", "brand.accent", "status.info"],
        wcag_criteria=["WCAG 2.2 1.3.1 (Info and Relationships)"],
        has_interactive_states=True,
    ),
    ComponentDefinitionContract(
        name="SearchBar",
        taxonomy=ComponentTaxonomy.LEVEL_3_COMPOSITE,
        description="Composed search experience uniting input, clear trigger, and filter drawer button.",
        available_variants=["header", "standalone"],
        available_sizes=["md", "lg"],
        design_tokens_used=["surface.secondary", "border.default", "target.min_touch"],
        wcag_criteria=["WCAG 2.2 3.3.2 (Labels or Instructions)"],
        has_interactive_states=True,
    ),
    ComponentDefinitionContract(
        name="FilterBar",
        taxonomy=ComponentTaxonomy.LEVEL_3_COMPOSITE,
        description="Faceting toolbar displaying active filter chips, tally count, and clear all trigger.",
        available_variants=["horizontal", "sticky"],
        available_sizes=["sm", "md"],
        design_tokens_used=["surface.primary", "space.2", "border.subtle"],
        wcag_criteria=["WCAG 2.2 4.1.2 (Name, Role, Value)"],
        has_interactive_states=True,
    ),
    ComponentDefinitionContract(
        name="ActionBar",
        taxonomy=ComponentTaxonomy.LEVEL_3_COMPOSITE,
        description="Fixed screen action toolbar coordinating primary CTA, secondary action, and price summary.",
        available_variants=["floating", "fixed_bottom"],
        available_sizes=["md"],
        design_tokens_used=["surface.primary", "elevation.4", "target.min_touch"],
        wcag_criteria=["WCAG 2.2 2.5.8 (Target Size >= 44px)"],
        has_interactive_states=True,
    ),
]

_CANONICAL_CATALOG = ComponentCatalogContract(
    primitives=PRIMITIVE_COMPONENTS,
    core_ui=CORE_UI_COMPONENTS,
    composites=COMPOSITE_COMPONENTS,
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

SPEC_MAP: dict[str, Any] = {
    # L1 Primitives
    "box": BoxSpecContract,
    "stack": StackSpecContract,
    "inline": InlineSpecContract,
    "grid": GridSpecContract,
    "container": ContainerSpecContract,
    "button": ButtonSpecContract,
    "iconbutton": IconButtonSpecContract,
    "link": LinkSpecContract,
    "input": InputSpecContract,
    "badge": BadgeSpecContract,
    "chip": ChipSpecContract,
    "typography": TypographySpecContract,
    "skeleton": SkeletonSpecContract,
    # L2 Core UI
    "card": CardSpecContract,
    "avatar": AvatarSpecContract,
    "modal": ModalSpecContract,
    "drawer": DrawerSpecContract,
    "dialogconfirm": DialogConfirmSpecContract,
    "alert": AlertSpecContract,
    "rating": RatingSpecContract,
    "price": PriceSpecContract,
    "quantitycontrol": QuantityControlSpecContract,
    "pagination": PaginationSpecContract,
    "progress": ProgressSpecContract,
    "segmentedcontrol": SegmentedControlSpecContract,
    "formfield": FormFieldSpecContract,
    "emptystate": EmptyStateSpecContract,
    "errorstate": ErrorStateSpecContract,
    # L3 Composites
    "productcard": ProductCardSpecContract,
    "fashioncard": FashionCardSpecContract,
    "lookcard": LookCardSpecContract,
    "collectioncard": CollectionCardSpecContract,
    "recommendationcard": RecommendationCardSpecContract,
    "searchbar": SearchBarSpecContract,
    "filterbar": FilterBarSpecContract,
    "actionbar": ActionBarSpecContract,
}


def validate_component_props(
    component_name: str,
    props: dict[str, Any],
) -> ComponentValidationReportContract:
    """Validate runtime props against the component's strict contract."""
    clean_name = component_name.lower().replace(" ", "").replace("_", "").replace("-", "")
    schema_cls = SPEC_MAP.get(clean_name)

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
