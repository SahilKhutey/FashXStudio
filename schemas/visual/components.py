"""FashXStudio Component Framework Contracts — Phase 05.

Defines Pydantic v2 data contracts for Level 1 (Primitives) and Level 2 (Core UI)
components in the FashXStudio Component Framework:
- Buttons, Inputs, Typography, Badges, Icons, Dividers, Skeletons, Spinners
- Cards, Modals, BottomSheets, Accordions, SegmentedControls, Ratings, FormFields
- Component catalog, prop specifications, token mappings, accessibility criteria

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
    """Component taxonomy levels (Section 0.2 & Phase 05)."""
    LEVEL_1_PRIMITIVE = "level_1_primitive"
    LEVEL_2_CORE_UI = "level_2_core_ui"
    LEVEL_3_DOMAIN = "level_3_domain"
    LEVEL_4_FEATURE = "level_4_feature"


class ButtonVariant(StrEnum):
    """Button visual variants."""
    PRIMARY = "primary"
    SECONDARY = "secondary"
    OUTLINE = "outline"
    GHOST = "ghost"
    DESTRUCTIVE = "destructive"


class ComponentSize(StrEnum):
    """Standard component sizing scale."""
    SM = "sm"
    MD = "md"
    LG = "lg"


class InputType(StrEnum):
    """Input field formats."""
    TEXT = "text"
    SEARCH = "search"
    EMAIL = "email"
    PASSWORD = "password"
    NUMBER = "number"
    PHONE = "phone"


class BadgeVariant(StrEnum):
    """Badge and Tag visual color variants."""
    DEFAULT = "default"
    BRAND = "brand"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    ACCENT = "accent"
    NEUTRAL = "neutral"
    OUTLINE = "outline"


class CardVariant(StrEnum):
    """Card surface variants."""
    ELEVATED = "elevated"
    OUTLINED = "outlined"
    FILLED = "filled"


class TypographyRole(StrEnum):
    """Typography functional hierarchy roles."""
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
    """Skeleton placeholder shapes."""
    RECTANGLE = "rectangle"
    ROUNDED = "rounded"
    CIRCLE = "circle"
    TEXT = "text"


# ---------------------------------------------------------------------------
# Level 1: Primitive Specifications
# ---------------------------------------------------------------------------

class ButtonSpecContract(BaseContractModel):
    """Button component specification contract."""
    variant: ButtonVariant = Field(default=ButtonVariant.PRIMARY)
    size: ComponentSize = Field(default=ComponentSize.MD)
    label: str = Field(..., description="Accessible label text")
    icon: str | None = Field(default=None, description="Optional icon key")
    icon_position: str = Field(default="left", description="left | right")
    is_loading: bool = Field(default=False)
    is_disabled: bool = Field(default=False)
    is_full_width: bool = Field(default=False)
    min_touch_target_px: int = Field(default=44, description="WCAG 2.2 AA target size (>= 44px)")


class InputSpecContract(BaseContractModel):
    """TextInput component specification contract."""
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
    """Badge / Tag component specification contract."""
    label: str = Field(..., description="Badge content text")
    variant: BadgeVariant = Field(default=BadgeVariant.DEFAULT)
    size: ComponentSize = Field(default=ComponentSize.MD)
    is_pill: bool = Field(default=True)
    is_dismissible: bool = Field(default=False)
    icon: str | None = Field(default=None)


class TypographySpecContract(BaseContractModel):
    """Typography text component specification contract."""
    role: TypographyRole = Field(default=TypographyRole.BODY_M)
    text: str = Field(..., description="Text content to display")
    color_token: str = Field(default="content.primary")
    align: str = Field(default="left", description="left | center | right | justify")
    max_lines: int | None = Field(default=None)


class SkeletonSpecContract(BaseContractModel):
    """Skeleton loader component specification contract."""
    shape: SkeletonShape = Field(default=SkeletonShape.RECTANGLE)
    width: str | int = Field(default="100%")
    height: str | int = Field(default=16)
    border_radius: int = Field(default=4)
    is_animated: bool = Field(default=True)


# ---------------------------------------------------------------------------
# Level 2: Core UI Specifications
# ---------------------------------------------------------------------------

class CardSpecContract(BaseContractModel):
    """Card surface container specification contract."""
    variant: CardVariant = Field(default=CardVariant.ELEVATED)
    elevation: int = Field(default=1, ge=0, le=5)
    padding: str = Field(default="space.component", description="Padding token reference")
    is_clickable: bool = Field(default=False)
    is_hoverable: bool = Field(default=True)
    border_radius: str = Field(default="radius.md")


class ModalSpecContract(BaseContractModel):
    """Modal / Dialog specification contract."""
    title: str | None = Field(default=None)
    size: ComponentSize = Field(default=ComponentSize.MD)
    is_dismissible: bool = Field(default=True)
    has_scrim: bool = Field(default=True)
    has_focus_trap: bool = Field(default=True)
    accessibility_role: str = Field(default="dialog")


class RatingSpecContract(BaseContractModel):
    """Star rating and fit feedback specification contract."""
    value: float = Field(default=0.0, ge=0.0, le=5.0)
    max_stars: int = Field(default=5)
    allow_half: bool = Field(default=True)
    show_score: bool = Field(default=True)
    is_readonly: bool = Field(default=True)
    rating_count: int | None = Field(default=None)


class SegmentedControlOptionContract(BaseContractModel):
    """Option entry for SegmentedControl."""
    id: str
    label: str
    icon: str | None = Field(default=None)
    badge: str | None = Field(default=None)


class SegmentedControlSpecContract(BaseContractModel):
    """SegmentedControl / ToggleGroup specification contract."""
    options: list[SegmentedControlOptionContract] = Field(..., min_length=2)
    selected_id: str
    size: ComponentSize = Field(default=ComponentSize.MD)
    is_full_width: bool = Field(default=True)


class FormFieldSpecContract(BaseContractModel):
    """Composite FormField specification contract."""
    field_id: str
    label: str
    is_required: bool = Field(default=False)
    helper_text: str | None = Field(default=None)
    error_text: str | None = Field(default=None)
    state: str = Field(default="default", description="default | focus | error | success | disabled")


# ---------------------------------------------------------------------------
# Component Catalog & Metadata
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

    @property
    def total_components(self) -> int:
        return len(self.primitives) + len(self.core_ui)

    def find_component(self, name: str) -> ComponentDefinitionContract | None:
        for c in self.primitives + self.core_ui:
            if c.name.lower() == name.lower():
                return c
        return None


class ComponentValidationReportContract(BaseContractModel):
    """Validation response for component props."""
    is_valid: bool
    component_name: str
    errors: list[str] = Field(default_factory=list)
    validated_props: dict[str, Any] = Field(default_factory=dict)
