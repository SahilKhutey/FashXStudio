"""FashXStudio Visual Layer Contracts — Version 1.

Governs the screen inventory, route registry, responsive layouts,
interaction state models, page templates, dependency groups,
and the 17-point Screen Specification Contract for the Screens / Pages / Visual Design subsystem.
Enforces Constitution Rule I02 (Contract Primacy) with extra="forbid".
"""

from enum import StrEnum
from typing import Any
from pydantic import Field
from schemas.base import BaseContractModel


class ScreenDomain(StrEnum):
    # Core Experience Domains (Visual Design — 1)
    PLATFORM = "platform"
    HOME = "home"
    DISCOVERY = "discovery"
    SEARCH = "search"
    PRODUCT = "product"
    SHOPPING = "shopping"
    FASHION = "fashion"
    STYLE = "style"
    TRENDS = "trends"
    REGIONAL = "regional"
    AI = "ai"
    PROFILE = "profile"
    SYSTEM = "system"
    # Aliases / Subdomain compatibility
    ONBOARDING = "onboarding"
    VTO = "vto"
    CLOSET = "closet"
    OUTFIT = "outfit"
    INTELLIGENCE = "intelligence"
    ADMIN = "admin"


class PageTemplateType(StrEnum):
    """The 11 Reusable Page Templates (Visual Design — 1 Section 1.24)."""
    LISTING = "listing"
    DETAIL = "detail"
    DISCOVERY = "discovery"
    EDITORIAL = "editorial"
    BUILDER = "builder"
    MAP = "map"
    DASHBOARD = "dashboard"
    ASSISTANT = "assistant"
    COMPARISON = "comparison"
    CHECKOUT = "checkout"
    SETTINGS = "settings"


class ImplementationDependencyGroup(StrEnum):
    """Implementation Sequencing by Dependency Order (Visual Design — 1 Section 1.20)."""
    GROUP_A_FOUNDATION = "group_a_foundation"
    GROUP_B_CORE_CONTENT = "group_b_core_content"
    GROUP_C_ADVANCED_EXPERIENCES = "group_c_advanced_experiences"
    GROUP_D_PERSONALIZATION = "group_d_personalization"
    GROUP_E_PRODUCTION_QUALITY = "group_e_production_quality"


class NavigationType(StrEnum):
    TAB = "tab"
    STACK = "stack"
    MODAL = "modal"
    DRAWER = "drawer"


class DeviceBreakpoint(StrEnum):
    XS = "xs"  # < 480px (Compact Mobile)
    SM = "sm"  # 480px - 767px (Large Mobile / Phablet)
    MD = "md"  # 768px - 1023px (Tablet Portrait)
    LG = "lg"  # 1024px - 1279px (Tablet Landscape / Laptop)
    XL = "xl"  # >= 1280px (Desktop / 4K Displays)


class InteractionStateEnum(StrEnum):
    DEFAULT = "default"
    HOVER = "hover"
    FOCUS = "focus"
    ACTIVE = "active"
    SELECTED = "selected"
    DISABLED = "disabled"
    LOADING = "loading"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    EMPTY = "empty"
    OFFLINE = "offline"


class ComponentTaxonomyLevel(StrEnum):
    LEVEL_1_PRIMITIVE = "level_1_primitive"
    LEVEL_2_COMMON_UI = "level_2_common_ui"
    LEVEL_3_DOMAIN = "level_3_domain"
    LEVEL_4_FEATURE = "level_4_feature"


class FashionContentType(StrEnum):
    PRODUCT = "product"
    OUTFIT = "outfit"
    LOOK = "look"
    STYLE = "style"
    TREND = "trend"
    COLLECTION = "collection"
    BRAND = "brand"
    EDITORIAL = "editorial"
    RECOMMENDATION = "recommendation"


class ShoppingFunnelStage(StrEnum):
    DISCOVER = "discover"
    UNDERSTAND = "understand"
    COMPARE = "compare"
    SELECT = "select"
    SAVE_CART = "save_cart"
    PURCHASE_FLOW = "purchase_flow"


class MapLayerType(StrEnum):
    GEOGRAPHIC = "geographic"
    REGIONAL_DATA = "regional_data"
    FASHION_SHOPPING = "fashion_shopping"


class AiInteractionStage(StrEnum):
    USER_INPUT = "user_input"
    PROCESSING = "processing"
    AI_RESULT = "ai_result"
    EXPLANATION_CONTEXT = "explanation_context"
    USER_CONTROLS = "user_controls"
    USER_ACTION = "user_action"


class ScreenDefinition(BaseContractModel):
    screen_id: str = Field(..., description="Unique screen identifier e.g. SCR-DISC-01 or P02")
    screen_code: str | None = Field(default=None, description="Short screen catalog code e.g. P02, A01, D01")
    title: str = Field(..., description="Human-readable screen title")
    domain: ScreenDomain = Field(..., description="Product domain classification")
    route: str = Field(..., description="Canonical route or deep-link path")
    navigation_type: NavigationType = Field(default=NavigationType.STACK, description="Presentation mode")
    feature_id: str = Field(..., description="Bound Feature Platform ID e.g. FX-F03")
    template_type: PageTemplateType = Field(default=PageTemplateType.DISCOVERY, description="Reusable page template")
    dependency_group: ImplementationDependencyGroup = Field(
        default=ImplementationDependencyGroup.GROUP_B_CORE_CONTENT,
        description="Implementation dependency sequence",
    )
    requires_auth: bool = Field(default=True, description="Whether authentication is required")
    requires_biometric_consent: bool = Field(default=False, description="Whether GDPR biometric consent is required")
    supported_breakpoints: list[DeviceBreakpoint] = Field(
        default_factory=lambda: [
            DeviceBreakpoint.XS,
            DeviceBreakpoint.SM,
            DeviceBreakpoint.MD,
            DeviceBreakpoint.LG,
            DeviceBreakpoint.XL,
        ]
    )
    description: str = Field("", description="Functional purpose of the screen")


class BreakpointConfig(BaseContractModel):
    breakpoint: DeviceBreakpoint
    min_width: int
    max_width: int | None = None
    columns: int
    gutter: int
    margin: int
    content_max_width: int | None = None


class ScreenInventoryRegistry(BaseContractModel):
    version: str = Field(default="1.0.0", description="Semantic contract version")
    total_screens: int = Field(..., description="Total count of registered screens")
    screens: list[ScreenDefinition] = Field(default_factory=list, description="Registered screen catalog")

    def get_screen(self, screen_id: str) -> ScreenDefinition | None:
        for s in self.screens:
            if s.screen_id == screen_id or s.screen_code == screen_id:
                return s
        return None

    def get_by_route(self, route: str) -> ScreenDefinition | None:
        for s in self.screens:
            if s.route == route:
                return s
        return None

    def get_by_domain(self, domain: ScreenDomain | str) -> list[ScreenDefinition]:
        return [s for s in self.screens if s.domain == domain]

    def get_by_template(self, template: PageTemplateType) -> list[ScreenDefinition]:
        return [s for s in self.screens if s.template_type == template]

    def get_by_dependency_group(self, group: ImplementationDependencyGroup) -> list[ScreenDefinition]:
        return [s for s in self.screens if s.dependency_group == group]


class ScreenSpecificationContract(BaseContractModel):
    """The 17-point Screen Specification Contract governing every FashXStudio screen."""
    screen_id: str = Field(..., description="1. Unique Screen ID e.g. P02 or SCR-DISC-01")
    screen_name: str = Field(..., description="2. Formal human-readable screen name")
    purpose: str = Field(..., description="3. Concise business/user purpose of the screen")
    user: str = Field(..., description="4. User persona or role target")
    entry_point: str = Field(..., description="5. Inbound entry route or trigger")
    exit_point: str = Field(..., description="6. Outbound exit paths or dismissal")
    primary_action: str = Field(..., description="7. Primary call-to-action")
    secondary_actions: list[str] = Field(default_factory=list, description="8. Secondary actions")
    data_sources: list[str] = Field(default_factory=list, description="9. Required API endpoints / data stores")
    components: list[str] = Field(default_factory=list, description="10. Mapped UI & domain components")
    states: list[InteractionStateEnum] = Field(default_factory=list, description="11. Handled interaction states")
    responsive_rules: dict[str, str] = Field(default_factory=dict, description="12. Viewport adaptation rules")
    accessibility: dict[str, str] = Field(default_factory=dict, description="13. WCAG & a11y criteria")
    error_handling: dict[str, str] = Field(default_factory=dict, description="14. Error boundaries & fallbacks")
    analytics_events: list[str] = Field(default_factory=list, description="15. Emitted telemetry events")
    dependencies: list[str] = Field(default_factory=list, description="16. Required platform features/capabilities")
    test_cases: list[str] = Field(default_factory=list, description="17. Test case identifiers")
