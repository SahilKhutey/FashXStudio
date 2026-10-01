"""FashXStudio Component Framework Contracts — Phase 05.

Defines Pydantic v2 data contracts for the 5-layer Component Architecture (Sections 5.1-5.72):
- L1 Primitives: Box, Stack, Inline, Grid, Container, Center, Split, AspectRatio, ScrollArea, VisuallyHidden, Divider
- L2 Core UI: Button, IconButton, Link, Input, FormField, Card, Avatar, Badge, Chip, Alert, Toast, Modal, Drawer, DialogConfirm, Rating, Price, QuantityControl, Pagination, Progress, Skeleton, Tooltip, Popover, EmptyState, ErrorState
- L3 Composite Components: ProductCard, FashionCard, LookCard, CollectionCard, RecommendationCard, SearchBar, FilterBar, ActionBar
- L4 UI Patterns: ProductGridPattern, FilterPanelPattern, ListingToolbarPattern
- Catalog & Validation Engine

All schemas enforce extra="forbid" via BaseContractModel (Constitution Rule I02).
"""

from enum import StrEnum
from typing import Any
from pydantic import Field
from schemas.base import BaseContractModel


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class ComponentTaxonomy(StrEnum):
    """Component taxonomy layers (Section 5.2)."""
    LEVEL_0_TOKENS = "level_0_tokens"
    LEVEL_1_PRIMITIVE = "level_1_primitive"
    LEVEL_2_CORE_UI = "level_2_core_ui"
    LEVEL_3_COMPOSITE = "level_3_composite"
    LEVEL_4_PATTERN = "level_4_pattern"
    LEVEL_3_DOMAIN = "level_3_domain"    # alias for backwards compatibility
    LEVEL_4_FEATURE = "level_4_feature"  # alias for backwards compatibility


class ButtonVariant(StrEnum):
    """Button visual variants (Section 5.11)."""
    PRIMARY = "primary"
    SECONDARY = "secondary"
    TERTIARY = "tertiary"
    OUTLINE = "outline"
    GHOST = "ghost"
    DESTRUCTIVE = "destructive"


class ComponentSize(StrEnum):
    """Standard component sizing scale."""
    SM = "sm"
    MD = "md"
    LG = "lg"


class InputType(StrEnum):
    """Input field formats (Section 5.14)."""
    TEXT = "text"
    SEARCH = "search"
    EMAIL = "email"
    PASSWORD = "password"
    NUMBER = "number"
    PHONE = "phone"
    TEXTAREA = "textarea"


class BadgeVariant(StrEnum):
    """Badge and Tag visual color variants (Section 5.23)."""
    DEFAULT = "default"
    BRAND = "brand"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    ACCENT = "accent"
    NEUTRAL = "neutral"
    OUTLINE = "outline"
    INFO = "info"


class CardVariant(StrEnum):
    """Card surface variants (Section 5.19)."""
    DEFAULT = "default"
    ELEVATED = "elevated"
    OUTLINED = "outlined"
    FILLED = "filled"
    INTERACTIVE = "interactive"
    COMPACT = "compact"
    MEDIA = "media"


class TypographyRole(StrEnum):
    """Typography functional hierarchy roles (Section 5.9)."""
    DISPLAY_XL = "display_xl"
    DISPLAY_L = "display_l"
    DISPLAY_M = "display_m"
    HEADING_XL = "heading_xl"
    HEADING_L = "heading_l"
    HEADING_M = "heading_m"
    HEADING_S = "heading_s"
    HEADING_XS = "heading_xs"
    BODY_L = "body_l"
    BODY_M = "body_m"
    BODY_S = "body_s"
    LABEL_L = "label_l"
    LABEL_M = "label_m"
    LABEL_S = "label_s"
    CAPTION = "caption"
    OVERLINE = "overline"


class SkeletonShape(StrEnum):
    """Skeleton placeholder shapes (Section 5.36)."""
    RECTANGLE = "rectangle"
    ROUNDED = "rounded"
    CIRCLE = "circle"
    TEXT = "text"


class AlertVariant(StrEnum):
    """Alert severity notification types (Section 5.31)."""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


class ProgressVariant(StrEnum):
    """Progress indicator types (Section 5.32)."""
    LINEAR = "linear"
    CIRCULAR = "circular"
    STEPPER = "stepper"


class ImageFitMode(StrEnum):
    """Image display fit mode (Section 5.20)."""
    CONTAIN = "contain"
    COVER = "cover"
    FILL = "fill"


# ---------------------------------------------------------------------------
# L1: Primitive Specifications (Section 5.3 - 5.10)
# ---------------------------------------------------------------------------

class BoxSpecContract(BaseContractModel):
    """Box layout primitive specification (Section 5.4)."""
    padding: str = Field(default="space.0")
    margin: str = Field(default="space.0")
    background_token: str = Field(default="surface.primary")
    border_radius_token: str = Field(default="radius.none")
    border_color_token: str | None = Field(default=None)
    border_width: int = Field(default=0)


class StackSpecContract(BaseContractModel):
    """Stack vertical layout specification (Section 5.5)."""
    gap: str = Field(default="space.component.md")
    align: str = Field(default="stretch", description="stretch | flex-start | center | flex-end")
    is_reversed: bool = Field(default=False)


class InlineSpecContract(BaseContractModel):
    """Inline horizontal layout specification (Section 5.6)."""
    gap: str = Field(default="space.2")
    align: str = Field(default="center", description="center | flex-start | flex-end | baseline")
    justify: str = Field(default="flex-start", description="flex-start | center | flex-end | space-between")
    wrap: bool = Field(default=True)


class GridSpecContract(BaseContractModel):
    """Responsive Grid layout specification (Section 5.7)."""
    columns: int = Field(default=4, ge=1, le=12)
    gutter: str = Field(default="space.4")
    min_column_width_px: int = Field(default=240)


class ContainerSpecContract(BaseContractModel):
    """Content Container layout specification (Section 5.8)."""
    max_width_px: int = Field(default=1280)
    horizontal_padding_token: str = Field(default="space.component")
    is_centered: bool = Field(default=True)


class AspectRatioSpecContract(BaseContractModel):
    """Aspect ratio container specification."""
    ratio: float = Field(default=1.0, gt=0.0)


# ---------------------------------------------------------------------------
# L2: Core Components Specifications (Section 5.11 - 5.49)
# ---------------------------------------------------------------------------

class ButtonSpecContract(BaseContractModel):
    """Button component specification contract (Section 5.11 & 5.12)."""
    variant: ButtonVariant = Field(default=ButtonVariant.PRIMARY)
    size: ComponentSize = Field(default=ComponentSize.MD)
    label: str = Field(..., description="Accessible label text")
    icon: str | None = Field(default=None, description="Optional icon key")
    icon_position: str = Field(default="left", description="left | right")
    is_loading: bool = Field(default=False)
    is_disabled: bool = Field(default=False)
    is_full_width: bool = Field(default=False)
    min_touch_target_px: int = Field(default=44, description="WCAG 2.2 AA target size (>= 44px)")


class IconButtonSpecContract(BaseContractModel):
    """Icon-only button specification (Section 5.13)."""
    icon: str = Field(..., description="Icon glyph or name")
    accessibility_label: str = Field(..., description="Required accessible name (WCAG 2.2 4.1.2)")
    size: ComponentSize = Field(default=ComponentSize.MD)
    variant: ButtonVariant = Field(default=ButtonVariant.GHOST)
    is_disabled: bool = Field(default=False)
    min_touch_target_px: int = Field(default=44)


class LinkSpecContract(BaseContractModel):
    """Link navigation component specification (Section 5.10)."""
    href: str = Field(..., description="Target route or URL")
    label: str = Field(..., description="Link display text")
    is_external: bool = Field(default=False)
    variant: str = Field(default="default", description="default | subtle | underline")


class InputSpecContract(BaseContractModel):
    """TextInput component specification contract (Section 5.14 & 5.15)."""
    input_type: InputType = Field(default=InputType.TEXT)
    label: str | None = Field(default=None)
    placeholder: str | None = Field(default=None)
    helper_text: str | None = Field(default=None)
    error_text: str | None = Field(default=None)
    is_disabled: bool = Field(default=False)
    is_readonly: bool = Field(default=False)
    is_required: bool = Field(default=False)
    leading_icon: str | None = Field(default=None)
    trailing_icon: str | None = Field(default=None)
    show_clear_button: bool = Field(default=True)


class BadgeSpecContract(BaseContractModel):
    """Badge component specification contract (Section 5.23)."""
    label: str = Field(..., description="Badge content text")
    variant: BadgeVariant = Field(default=BadgeVariant.DEFAULT)
    size: ComponentSize = Field(default=ComponentSize.MD)
    is_pill: bool = Field(default=True)
    is_dismissible: bool = Field(default=False)
    icon: str | None = Field(default=None)


class ChipSpecContract(BaseContractModel):
    """Tag / Chip component specification (Section 5.24)."""
    label: str = Field(..., description="Filter/attribute chip text")
    is_selected: bool = Field(default=False)
    is_removable: bool = Field(default=False)
    icon: str | None = Field(default=None)
    value: str | None = Field(default=None)


class TypographySpecContract(BaseContractModel):
    """Typography text component specification contract (Section 5.9)."""
    role: TypographyRole = Field(default=TypographyRole.BODY_M)
    text: str = Field(..., description="Text content to display")
    color_token: str = Field(default="content.primary")
    align: str = Field(default="left", description="left | center | right | justify")
    max_lines: int | None = Field(default=None)


class SkeletonSpecContract(BaseContractModel):
    """Skeleton loader component specification contract (Section 5.36)."""
    shape: SkeletonShape = Field(default=SkeletonShape.RECTANGLE)
    width: str | int = Field(default="100%")
    height: str | int = Field(default=16)
    border_radius: int = Field(default=4)
    is_animated: bool = Field(default=True)


class CardSpecContract(BaseContractModel):
    """Card surface container specification contract (Section 5.18 & 5.19)."""
    variant: CardVariant = Field(default=CardVariant.ELEVATED)
    elevation: int = Field(default=1, ge=0, le=5)
    padding: str = Field(default="space.component", description="Padding token reference")
    is_clickable: bool = Field(default=False)
    is_hoverable: bool = Field(default=True)
    border_radius: str = Field(default="radius.md")


class AvatarSpecContract(BaseContractModel):
    """Avatar component specification (Section 5.22)."""
    image_uri: str | None = Field(default=None)
    initials: str | None = Field(default=None)
    size: ComponentSize = Field(default=ComponentSize.MD)
    accessibility_label: str = Field(default="User Avatar")
    is_verified: bool = Field(default=False)


class ModalSpecContract(BaseContractModel):
    """Modal / Dialog specification contract (Section 5.27)."""
    title: str | None = Field(default=None)
    size: ComponentSize = Field(default=ComponentSize.MD)
    is_dismissible: bool = Field(default=True)
    has_scrim: bool = Field(default=True)
    has_focus_trap: bool = Field(default=True)
    accessibility_role: str = Field(default="dialog")


class DrawerSpecContract(BaseContractModel):
    """Drawer panel specification contract (Section 5.28)."""
    title: str | None = Field(default=None)
    position: str = Field(default="left", description="left | right | bottom")
    is_open: bool = Field(default=False)
    has_scrim: bool = Field(default=True)


class DialogConfirmSpecContract(BaseContractModel):
    """Confirmation Dialog specification (Section 5.29)."""
    title: str = Field(..., description="Consequential dialog title")
    message: str = Field(..., description="Action impact explanation")
    confirm_label: str = Field(default="Confirm")
    cancel_label: str = Field(default="Cancel")
    is_destructive: bool = Field(default=False)


class AlertSpecContract(BaseContractModel):
    """Alert persistent notification specification (Section 5.31)."""
    variant: AlertVariant = Field(default=AlertVariant.INFO)
    title: str | None = Field(default=None)
    message: str = Field(..., description="Alert text message")
    action_label: str | None = Field(default=None)
    is_dismissible: bool = Field(default=False)


class ProgressSpecContract(BaseContractModel):
    """Progress indicator specification (Section 5.32)."""
    variant: ProgressVariant = Field(default=ProgressVariant.LINEAR)
    value: float = Field(default=0.0, ge=0.0, le=100.0, description="Percentage 0-100")
    is_indeterminate: bool = Field(default=False)


class RatingSpecContract(BaseContractModel):
    """Star rating specification contract (Section 5.40)."""
    value: float = Field(default=0.0, ge=0.0, le=5.0)
    max_stars: int = Field(default=5)
    allow_half: bool = Field(default=True)
    show_score: bool = Field(default=True)
    is_readonly: bool = Field(default=True)
    rating_count: int | None = Field(default=None)


class PriceSpecContract(BaseContractModel):
    """Standardized Price Display specification (Section 5.41)."""
    amount: float = Field(..., ge=0.0, description="Current price")
    original_amount: float | None = Field(default=None, description="Strikethrough list price")
    currency: str = Field(default="INR", description="Currency symbol or ISO code")
    currency_symbol: str = Field(default="₹")
    discount_percentage: int | None = Field(default=None)


class QuantityControlSpecContract(BaseContractModel):
    """Quantity stepper control specification (Section 5.42)."""
    value: int = Field(default=1, ge=1)
    min_value: int = Field(default=1)
    max_value: int = Field(default=99)
    is_disabled: bool = Field(default=False)


class PaginationSpecContract(BaseContractModel):
    """Pagination navigation control specification (Section 5.43)."""
    current_page: int = Field(default=1, ge=1)
    total_pages: int = Field(..., ge=1)
    show_prev_next: bool = Field(default=True)


class EmptyStateSpecContract(BaseContractModel):
    """Empty State view contract (Section 5.34)."""
    icon: str = Field(default="♡")
    title: str = Field(..., description="What is empty")
    description: str = Field(..., description="Why it matters")
    action_label: str | None = Field(default=None, description="What user can do next")
    action_route: str | None = Field(default=None)


class ErrorStateSpecContract(BaseContractModel):
    """Error State view contract (Section 5.35)."""
    title: str = Field(default="Something went wrong.")
    message: str = Field(..., description="Meaningful message")
    retry_label: str = Field(default="Try Again")
    recovery_label: str | None = Field(default=None)
    recovery_route: str | None = Field(default=None)


class SegmentedControlOptionContract(BaseContractModel):
    """Option entry for SegmentedControl (Section 5.46)."""
    id: str
    label: str
    icon: str | None = Field(default=None)
    badge: str | None = Field(default=None)


class SegmentedControlSpecContract(BaseContractModel):
    """SegmentedControl / ToggleGroup specification contract (Section 5.46)."""
    options: list[SegmentedControlOptionContract] = Field(..., min_length=2)
    selected_id: str
    size: ComponentSize = Field(default=ComponentSize.MD)
    is_full_width: bool = Field(default=True)


class FormFieldSpecContract(BaseContractModel):
    """Composite FormField specification contract (Section 5.16)."""
    field_id: str
    label: str
    is_required: bool = Field(default=False)
    helper_text: str | None = Field(default=None)
    error_text: str | None = Field(default=None)
    state: str = Field(default="default", description="default | focus | error | success | disabled")


# ---------------------------------------------------------------------------
# L3: Composite Components Specifications (Section 5.50 - 5.55)
# ---------------------------------------------------------------------------

class ProductCardSpecContract(BaseContractModel):
    """Product Card commerce composite specification (Section 5.51)."""
    product_id: str
    title: str
    brand: str
    image_uri: str
    price: PriceSpecContract
    rating: RatingSpecContract | None = Field(default=None)
    is_saved: bool = Field(default=False)
    is_in_stock: bool = Field(default=True)
    badge: str | None = Field(default=None)


class FashionCardSpecContract(BaseContractModel):
    """Fashion Editorial Card composite specification (Section 5.52)."""
    story_id: str
    title: str
    story_category: str
    image_uri: str
    description: str | None = Field(default=None)


class LookCardSpecContract(BaseContractModel):
    """Look Card composite specification (Section 5.53)."""
    look_id: str
    title: str
    image_uri: str
    items_count: int = Field(default=1, ge=1)
    is_saved: bool = Field(default=False)


class CollectionCardSpecContract(BaseContractModel):
    """Collection Card composite specification (Section 5.54)."""
    collection_id: str
    title: str
    image_uri: str
    product_count: int = Field(default=0, ge=0)
    cta_label: str = Field(default="Explore →")


class RecommendationCardSpecContract(BaseContractModel):
    """AI Recommendation Card composite specification (Section 5.55)."""
    recommendation_id: str
    product: ProductCardSpecContract
    explanation: str = Field(..., description="Why this appears (Explainability)")
    confidence_score: float | None = Field(default=None, ge=0.0, le=1.0)


class SearchBarSpecContract(BaseContractModel):
    """Search Bar composite specification (Section 5.47 & 5.50)."""
    placeholder: str = Field(default="Search products, styles, trends…")
    initial_query: str = Field(default="")
    show_filter_button: bool = Field(default=True)


class FilterBarSpecContract(BaseContractModel):
    """Filter Bar composite specification (Section 5.48 & 5.50)."""
    active_chips: list[ChipSpecContract] = Field(default_factory=list)
    show_clear_all: bool = Field(default=True)
    filter_count: int = Field(default=0)


class ActionBarSpecContract(BaseContractModel):
    """Bottom / Top Action Bar composite specification."""
    primary_action: ButtonSpecContract
    secondary_action: ButtonSpecContract | None = Field(default=None)
    price_summary: PriceSpecContract | None = Field(default=None)


# ---------------------------------------------------------------------------
# L4: UI Patterns Specifications (Section 5.50 & 5.56)
# ---------------------------------------------------------------------------

class ProductGridPatternContract(BaseContractModel):
    """Product Grid composite pattern (Section 5.56)."""
    columns_desktop: int = Field(default=4)
    columns_tablet: int = Field(default=3)
    columns_mobile: int = Field(default=2)
    gutter: str = Field(default="space.4")
    products: list[ProductCardSpecContract] = Field(default_factory=list)


class FilterPanelPatternContract(BaseContractModel):
    """Filter Panel composite pattern (Section 5.48)."""
    panel_title: str = Field(default="Filters")
    categories: list[str] = Field(default_factory=list)
    brands: list[str] = Field(default_factory=list)
    price_min: float | None = Field(default=None)
    price_max: float | None = Field(default=None)


# ---------------------------------------------------------------------------
# Component Catalog & Metadata (Section 5.62 & 5.63)
# ---------------------------------------------------------------------------

class ComponentDefinitionContract(BaseContractModel):
    """Registered component metadata in the catalog."""
    name: str = Field(..., description="Unique component identifier (e.g., 'Button')")
    taxonomy: ComponentTaxonomy
    description: str
    available_variants: list[str] = Field(default_factory=list)
    available_sizes: list[str] = Field(default_factory=list)
    design_tokens_used: list[str] = Field(default_factory=list)
    wcag_criteria: list[str] = Field(default_factory=list)
    has_interactive_states: bool = Field(default=True)


class ComponentCatalogContract(BaseContractModel):
    """Complete catalog of components available in FashXStudio."""
    primitives: list[ComponentDefinitionContract] = Field(default_factory=list)
    core_ui: list[ComponentDefinitionContract] = Field(default_factory=list)
    composites: list[ComponentDefinitionContract] = Field(default_factory=list)

    @property
    def total_components(self) -> int:
        return len(self.primitives) + len(self.core_ui) + len(self.composites)

    def find_component(self, name: str) -> ComponentDefinitionContract | None:
        target = name.lower().replace("_", "").replace("-", "")
        for c in self.primitives + self.core_ui + self.composites:
            if c.name.lower().replace("_", "").replace("-", "") == target:
                return c
        return None


class ComponentValidationReportContract(BaseContractModel):
    """Validation response for component props."""
    is_valid: bool
    component_name: str
    errors: list[str] = Field(default_factory=list)
    validated_props: dict[str, Any] = Field(default_factory=dict)
