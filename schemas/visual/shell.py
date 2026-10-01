"""FashXStudio Application Shell Contracts — Phase 03.

Defines Pydantic v2 data contracts for the Global Application Shell, navigation model,
layout templates, overlay registry, toast notifications, page header variants,
and shell configuration. All schemas enforce extra="forbid" (Constitution Rule I02).
"""

from enum import StrEnum
from typing import Any
from pydantic import Field
from schemas.base import BaseContractModel


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class NavigationGroup(StrEnum):
    """Navigation grouping categories (Section 3.10)."""
    PRIMARY = "primary"
    PERSONAL = "personal"
    UTILITY = "utility"


class NavigationItemState(StrEnum):
    """All valid navigation item interaction states (Section 3.11)."""
    DEFAULT = "default"
    HOVER = "hover"
    FOCUS = "focus"
    ACTIVE = "active"
    SELECTED = "selected"
    DISABLED = "disabled"


class SidebarMode(StrEnum):
    """Desktop sidebar display modes (Section 3.12)."""
    EXPANDED = "expanded"
    COLLAPSED = "collapsed"
    HIDDEN = "hidden"


class MobileDrawerState(StrEnum):
    """Mobile navigation drawer states (Section 3.13)."""
    OPEN = "open"
    CLOSED = "closed"
    ANIMATING = "animating"


class ShellLayoutMode(StrEnum):
    """Active layout mode resolved from breakpoint (Section 3.29)."""
    DESKTOP = "desktop"   # >= lg (1024px): sidebar + header + main
    TABLET = "tablet"     # md (768-1023px): compact nav + header + main
    MOBILE = "mobile"     # xs/sm (<768px): mobile header + main + bottom nav


class PageHeaderVariant(StrEnum):
    """Page header display variant (Section 3.18)."""
    STANDARD = "standard"
    EDITORIAL = "editorial"
    LISTING = "listing"
    DETAIL = "detail"
    DASHBOARD = "dashboard"


class LayoutTemplate(StrEnum):
    """Application layout templates (Section 3.31)."""
    STANDARD = "standard"
    LISTING = "listing"
    DETAIL = "detail"
    EDITORIAL = "editorial"
    DASHBOARD = "dashboard"
    BUILDER = "builder"
    MAP = "map"
    ASSISTANT = "assistant"
    CHECKOUT = "checkout"


class OverlayType(StrEnum):
    """Global overlay types (Section 3.21)."""
    MODAL = "modal"
    DRAWER = "drawer"
    POPOVER = "popover"
    COMMAND = "command"
    CONFIRMATION = "confirmation"


class ToastType(StrEnum):
    """Toast notification severity types (Section 3.22)."""
    SUCCESS = "success"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class ShellLoadState(StrEnum):
    """Application shell-level loading states (Section 3.27 & 3.28)."""
    IDLE = "idle"
    LOADING = "loading"
    ERROR = "error"
    READY = "ready"


# ---------------------------------------------------------------------------
# Navigation Model (Section 3.34)
# ---------------------------------------------------------------------------

class NavigationItemContract(BaseContractModel):
    """Data-driven navigation item definition (Section 3.34)."""
    id: str = Field(..., description="Stable unique navigation item ID")
    label: str = Field(..., description="Display label for the navigation item")
    icon: str = Field(..., description="Icon identifier (e.g. 'home', 'compass')")
    route: str = Field(..., description="Destination route path")
    group: NavigationGroup = Field(..., description="Navigation group membership")
    is_visible: bool = Field(default=True, description="Visibility toggle (UI only)")
    requires_auth: bool = Field(default=False, description="Requires authenticated session")
    badge_count: int | None = Field(default=None, description="Notification badge count")
    state: NavigationItemState = Field(default=NavigationItemState.DEFAULT)


class NavigationGroupContract(BaseContractModel):
    """A labeled group containing navigation items."""
    group: NavigationGroup
    label: str
    items: list[NavigationItemContract]


class NavigationConfigContract(BaseContractModel):
    """Full application navigation configuration (Section 3.10)."""
    primary: list[NavigationItemContract] = Field(default_factory=list)
    personal: list[NavigationItemContract] = Field(default_factory=list)
    bottom_bar_ids: list[str] = Field(
        default_factory=list,
        description="Ordered IDs of items to appear in mobile bottom navigation (max 5)",
    )

    @property
    def bottom_bar_items(self) -> list[NavigationItemContract]:
        all_items = self.primary + self.personal
        id_set = set(self.bottom_bar_ids)
        ordered = {item.id: item for item in all_items if item.id in id_set}
        return [ordered[i] for i in self.bottom_bar_ids if i in ordered]


# ---------------------------------------------------------------------------
# Shell Configuration Contract (Section 3.33)
# ---------------------------------------------------------------------------

class AppHeaderContract(BaseContractModel):
    """Application header configuration (Section 3.8)."""
    brand_name: str = Field(default="FashXStudio")
    brand_logo_uri: str | None = Field(default=None)
    show_search: bool = Field(default=True)
    show_notifications: bool = Field(default=True)
    show_user_menu: bool = Field(default=True)
    notification_count: int = Field(default=0)
    is_sticky: bool = Field(default=True, description="Header sticks to viewport top on scroll")


class ApplicationShellContract(BaseContractModel):
    """Master application shell configuration (Section 3.33)."""
    navigation: NavigationConfigContract = Field(..., description="Navigation model")
    header: AppHeaderContract = Field(default_factory=AppHeaderContract)
    sidebar_mode: SidebarMode = Field(default=SidebarMode.EXPANDED)
    drawer_state: MobileDrawerState = Field(default=MobileDrawerState.CLOSED)
    layout_mode: ShellLayoutMode = Field(default=ShellLayoutMode.MOBILE)
    load_state: ShellLoadState = Field(default=ShellLoadState.IDLE)
    active_route: str = Field(default="/")
    theme_mode: str = Field(default="light")
    skip_nav_target: str = Field(default="#main-content")


# ---------------------------------------------------------------------------
# Page Header Contract (Section 3.17 & 3.18)
# ---------------------------------------------------------------------------

class BreadcrumbItemContract(BaseContractModel):
    """A single breadcrumb navigation entry."""
    label: str
    route: str
    is_current: bool = Field(default=False)


class PageActionContract(BaseContractModel):
    """An action button rendered in the page header or section header."""
    label: str
    action_id: str
    variant: str = Field(default="primary", description="primary | secondary | ghost | destructive")
    icon: str | None = Field(default=None)
    is_disabled: bool = Field(default=False)


class PageHeaderContract(BaseContractModel):
    """Standard page header specification (Section 3.17)."""
    variant: PageHeaderVariant = Field(default=PageHeaderVariant.STANDARD)
    title: str = Field(..., description="Primary page title")
    description: str | None = Field(default=None)
    breadcrumbs: list[BreadcrumbItemContract] = Field(default_factory=list)
    primary_action: PageActionContract | None = Field(default=None)
    secondary_actions: list[PageActionContract] = Field(default_factory=list)
    status_label: str | None = Field(default=None)
    result_count: int | None = Field(default=None, description="Listing variant: result count")
    visual_uri: str | None = Field(default=None, description="Editorial variant: large hero image")


# ---------------------------------------------------------------------------
# Overlay & Toast Contracts (Section 3.21 & 3.22)
# ---------------------------------------------------------------------------

class OverlayContract(BaseContractModel):
    """A registered overlay instance in the global OverlayManager."""
    overlay_id: str = Field(..., description="Unique overlay identifier")
    overlay_type: OverlayType
    title: str | None = Field(default=None)
    is_dismissible: bool = Field(default=True, description="Closes on backdrop click/Escape")
    has_focus_trap: bool = Field(default=True, description="Traps keyboard focus inside overlay")


class ToastContract(BaseContractModel):
    """A toast notification entry (Section 3.22)."""
    toast_id: str
    toast_type: ToastType = Field(default=ToastType.INFO)
    message: str
    action_label: str | None = Field(default=None)
    auto_dismiss_ms: int = Field(default=4000, description="0 = no auto dismiss")
    is_persistent: bool = Field(default=False, description="Must be manually dismissed")


class OverlayRegistryContract(BaseContractModel):
    """The live overlay stack managed by OverlayManager (Section 3.21)."""
    active_overlays: list[OverlayContract] = Field(default_factory=list)
    toast_queue: list[ToastContract] = Field(default_factory=list)

    @property
    def top_overlay(self) -> OverlayContract | None:
        return self.active_overlays[-1] if self.active_overlays else None


# ---------------------------------------------------------------------------
# Layout Primitive Contracts (Section 3.20)
# ---------------------------------------------------------------------------

class ContentSectionContract(BaseContractModel):
    """Reusable content section blueprint (Section 3.19)."""
    section_id: str
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    action: PageActionContract | None = Field(default=None)
    layout: str = Field(default="grid", description="grid | list | carousel | stack")
    density: str = Field(default="comfortable", description="comfortable | compact | spacious")


class PageContainerContract(BaseContractModel):
    """Page container layout specification (Section 3.16)."""
    max_width: str = Field(default="1280px")
    horizontal_padding: str = Field(default="space.component")
    use_sidebar_offset: bool = Field(
        default=True,
        description="Accounts for desktop sidebar width in layout calculation",
    )


class LayoutTemplateContract(BaseContractModel):
    """A specific layout template configuration (Section 3.31)."""
    template: LayoutTemplate
    page_header: PageHeaderContract | None = Field(default=None)
    container: PageContainerContract = Field(default_factory=PageContainerContract)
    sections: list[ContentSectionContract] = Field(default_factory=list)
    is_full_bleed: bool = Field(
        default=False,
        description="True for editorial, map, and builder templates",
    )
    scroll_behavior: str = Field(
        default="viewport",
        description="viewport | feature-local | none",
    )
