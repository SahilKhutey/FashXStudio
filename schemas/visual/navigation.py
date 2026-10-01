"""FashXStudio Navigation System Contracts — Phase 04.

Defines Pydantic v2 data contracts for the unified navigation system covering:
- Route registry with nested children
- Navigation item structure (id, label, icon, route, group, order, visibility, activeMatch)
- Navigation state model (currentRoute, activeItem, expandedGroups, drawer, sidebar)
- Tab groups (route-based and state-based)
- Context navigation (local per-page navigation)
- Navigation analytics events
- Feature-flag-gated navigation items
- Navigation guard / visibility results
- Breadcrumb chain (ordered, responsive)
- Navigation error / 404 contracts

All schemas enforce extra="forbid" via BaseContractModel (Constitution Rule I02).
"""

from enum import StrEnum
from typing import Any
from pydantic import Field, model_validator
from schemas.base import BaseContractModel


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class NavigationVisibility(StrEnum):
    """UI-level visibility of a navigation item (Section 4.28). Not an auth check."""
    VISIBLE = "visible"
    HIDDEN = "hidden"
    DISABLED = "disabled"
    RESTRICTED = "restricted"


class NavigationItemGroup(StrEnum):
    """Semantic navigation groups (Section 4.5)."""
    PRIMARY = "primary"
    PERSONAL = "personal"
    UTILITY = "utility"


class NavigationPresentation(StrEnum):
    """Visual presentation mode of a navigation surface (Section 4.34)."""
    DESKTOP_EXPANDED = "desktop_expanded"
    DESKTOP_COLLAPSED = "desktop_collapsed"
    TABLET = "tablet"
    MOBILE_HEADER = "mobile_header"
    MOBILE_DRAWER = "mobile_drawer"
    MOBILE_BOTTOM = "mobile_bottom"


class TabMode(StrEnum):
    """Whether tab switching drives URL or local state (Section 4.18)."""
    ROUTE_BASED = "route_based"
    STATE_BASED = "state_based"


class NavigationEventType(StrEnum):
    """Structured navigation analytics events (Section 4.30)."""
    NAVIGATION_VIEW = "navigation_view"
    NAVIGATION_CLICK = "navigation_click"
    NAVIGATION_OPEN = "navigation_open"
    NAVIGATION_CLOSE = "navigation_close"
    BREADCRUMB_CLICK = "breadcrumb_click"
    TAB_CHANGE = "tab_change"
    BACK_NAVIGATION = "back_navigation"
    EXTERNAL_NAVIGATION = "external_navigation"
    SEARCH_NAVIGATION = "search_navigation"
    DEEP_LINK_ENTRY = "deep_link_entry"
    NAVIGATION_ERROR = "navigation_error"


class NavigationErrorCode(StrEnum):
    """Navigation error categories (Section 4.26 & 4.27)."""
    NOT_FOUND = "not_found"
    FORBIDDEN = "forbidden"
    DATA_FAILURE = "data_failure"
    FEATURE_DISABLED = "feature_disabled"


class NestedNavExpansion(StrEnum):
    """Expansion state for nested navigation groups (Section 4.10)."""
    COLLAPSED = "collapsed"
    EXPANDED = "expanded"
    ACTIVE_CHILD = "active_child"


# ---------------------------------------------------------------------------
# Route Registry Contract (Section 4.3 & 4.4)
# ---------------------------------------------------------------------------

class NavigationRouteContract(BaseContractModel):
    """A single registered route in the FashXStudio route registry (Section 4.4)."""
    id: str = Field(..., description="Stable unique route identifier")
    label: str = Field(..., description="Display label")
    icon: str = Field(..., description="Icon key from icon registry")
    route: str = Field(..., description="Absolute route path starting with '/'")
    group: NavigationItemGroup = Field(..., description="Navigation group membership")
    order: int = Field(..., description="Display order within the group (lower = first)")
    visibility: NavigationVisibility = Field(default=NavigationVisibility.VISIBLE)
    active_match: list[str] = Field(
        default_factory=list,
        description="Additional route prefixes that also set this item active",
    )
    is_external: bool = Field(default=False, description="Links to an external URL")
    requires_auth: bool = Field(default=False)
    feature_flag: str | None = Field(default=None, description="Feature flag key gating this item")
    children: list["NavigationRouteContract"] = Field(
        default_factory=list,
        description="Nested child routes for sub-navigation (Section 4.9)",
    )
    metadata: dict[str, Any] = Field(default_factory=dict)


# Pydantic v2 requires explicit model_rebuild for self-referencing models
NavigationRouteContract.model_rebuild()


class RouteRegistryContract(BaseContractModel):
    """The complete FashXStudio route registry (Section 4.3)."""
    routes: list[NavigationRouteContract] = Field(..., description="Flat + nested route list")

    @property
    def primary(self) -> list[NavigationRouteContract]:
        return [r for r in self.routes if r.group == NavigationItemGroup.PRIMARY]

    @property
    def personal(self) -> list[NavigationRouteContract]:
        return [r for r in self.routes if r.group == NavigationItemGroup.PERSONAL]

    def find_by_id(self, route_id: str) -> NavigationRouteContract | None:
        for r in self.routes:
            if r.id == route_id:
                return r
            for child in r.children:
                if child.id == route_id:
                    return child
        return None

    def find_by_route(self, route: str) -> NavigationRouteContract | None:
        for r in self.routes:
            if r.route == route or route in r.active_match:
                return r
            for child in r.children:
                if child.route == route or route in child.active_match:
                    return child
        return None


# ---------------------------------------------------------------------------
# Navigation State Contract (Section 4.37)
# ---------------------------------------------------------------------------

class NavigationStateContract(BaseContractModel):
    """Resolved navigation state for a given route and context (Section 4.37)."""
    current_route: str = Field(..., description="Current URL/route path")
    active_item_id: str | None = Field(default=None, description="ID of the active navigation item")
    active_parent_id: str | None = Field(default=None, description="Parent of active item if nested")
    expanded_group_ids: list[str] = Field(
        default_factory=list,
        description="IDs of navigation groups currently expanded",
    )
    mobile_drawer_open: bool = Field(default=False)
    sidebar_collapsed: bool = Field(default=False)
    focused_item_id: str | None = Field(default=None, description="Currently keyboard-focused item")
    presentation: NavigationPresentation = Field(default=NavigationPresentation.MOBILE_HEADER)
    navigation_history: list[str] = Field(
        default_factory=list,
        description="Recent route history (most recent last, max 20)",
    )


# ---------------------------------------------------------------------------
# Breadcrumb Contracts (Section 4.14 & 4.15)
# ---------------------------------------------------------------------------

class BreadcrumbEntryContract(BaseContractModel):
    """A single entry in a breadcrumb chain (Section 4.14)."""
    label: str
    route: str
    position: int = Field(..., description="1-based position in the chain")
    is_current: bool = Field(default=False, description="True for the final (current) segment")
    is_interactive: bool = Field(
        default=True,
        description="Current page breadcrumb should typically not be a link (Section 4.14)",
    )


class BreadcrumbChainContract(BaseContractModel):
    """An ordered breadcrumb chain with responsive adaptation metadata (Section 4.15)."""
    entries: list[BreadcrumbEntryContract] = Field(..., description="Ordered breadcrumb list")
    mobile_label: str = Field(
        ...,
        description="Mobile adaptive back label — the immediate parent's label",
    )
    is_truncated: bool = Field(
        default=False,
        description="True when intermediate segments are collapsed for deep hierarchies",
    )

    @property
    def current(self) -> BreadcrumbEntryContract | None:
        return next((e for e in self.entries if e.is_current), None)

    @property
    def parent(self) -> BreadcrumbEntryContract | None:
        ordered = [e for e in self.entries if not e.is_current]
        return ordered[-1] if ordered else None


# ---------------------------------------------------------------------------
# Tab System Contracts (Section 4.16, 4.17, 4.18)
# ---------------------------------------------------------------------------

class TabContract(BaseContractModel):
    """A single tab in a tab group (Section 4.17)."""
    id: str
    label: str
    route: str | None = Field(default=None, description="Route for route-based tabs")
    state_key: str | None = Field(default=None, description="State key for state-based tabs")
    is_active: bool = Field(default=False)
    is_disabled: bool = Field(default=False)
    badge_count: int | None = Field(default=None)
    icon: str | None = Field(default=None)

    @model_validator(mode="after")
    def route_or_state_key_required(self) -> "TabContract":
        if self.route is None and self.state_key is None:
            raise ValueError("TabContract requires either 'route' or 'state_key'")
        return self


class TabGroupContract(BaseContractModel):
    """A group of tabs for in-page or section navigation (Section 4.16)."""
    group_id: str
    label: str | None = Field(default=None, description="Accessible label for the tab list")
    mode: TabMode = Field(..., description="route_based or state_based")
    tabs: list[TabContract] = Field(..., min_length=2)

    @property
    def active_tab(self) -> TabContract | None:
        return next((t for t in self.tabs if t.is_active), None)


# ---------------------------------------------------------------------------
# Context Navigation (Section 4.19 & 4.20)
# ---------------------------------------------------------------------------

class ContextNavItemContract(BaseContractModel):
    """A local navigation item for within-page/section navigation (Section 4.19)."""
    id: str
    label: str
    route: str | None = Field(default=None)
    state_key: str | None = Field(default=None)
    is_active: bool = Field(default=False)
    is_disabled: bool = Field(default=False)


class ContextNavigationContract(BaseContractModel):
    """Local navigation for a page or section (Level 3/4 in Section 4.20)."""
    context_id: str = Field(..., description="Unique identifier for this nav context")
    label: str = Field(..., description="Accessible label for the nav region")
    items: list[ContextNavItemContract] = Field(..., min_length=2)
    mode: TabMode = Field(default=TabMode.ROUTE_BASED)

    @property
    def active_item(self) -> ContextNavItemContract | None:
        return next((i for i in self.items if i.is_active), None)


# ---------------------------------------------------------------------------
# Navigation Analytics (Section 4.30)
# ---------------------------------------------------------------------------

class NavigationAnalyticsEventContract(BaseContractModel):
    """Structured navigation analytics event (Section 4.30)."""
    event: NavigationEventType
    navigation_id: str | None = Field(default=None, description="ID of the navigation item")
    destination: str | None = Field(default=None, description="Target route")
    source_route: str | None = Field(default=None, description="Origin route")
    label: str | None = Field(default=None)
    metadata: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Navigation Guard (Section 4.28)
# ---------------------------------------------------------------------------

class NavigationGuardResultContract(BaseContractModel):
    """Result of a navigation visibility/access check (Section 4.28)."""
    item_id: str
    visibility: NavigationVisibility
    reason: str | None = Field(
        default=None,
        description="Human-readable reason for non-visible status",
    )
    redirect_route: str | None = Field(
        default=None,
        description="Alternative route to redirect to if restricted",
    )


# ---------------------------------------------------------------------------
# Feature Flag Navigation (Section 4.29)
# ---------------------------------------------------------------------------

class FeatureFlagNavContract(BaseContractModel):
    """Feature-flag gated navigation item resolution (Section 4.29)."""
    flag_key: str
    is_enabled: bool
    item_id: str
    resolved_visibility: NavigationVisibility


# ---------------------------------------------------------------------------
# Navigation Error States (Section 4.26 & 4.27)
# ---------------------------------------------------------------------------

class NavigationErrorContract(BaseContractModel):
    """Navigation error state for screen-level rendering (Section 4.26 & 4.27)."""
    error_code: NavigationErrorCode
    attempted_route: str
    user_message: str = Field(..., description="Human-readable error description")
    primary_recovery_route: str = Field(default="/", description="Primary recovery action route")
    primary_recovery_label: str = Field(default="Go Home")
    secondary_recovery_route: str | None = Field(default="/discover")
    secondary_recovery_label: str | None = Field(default="Explore Discover")


# ---------------------------------------------------------------------------
# Navigation Resolver Result (Section 4.1 & 4.2)
# ---------------------------------------------------------------------------

class NavigationResolverResultContract(BaseContractModel):
    """Full output of the navigation resolver for a route (Section 4.1)."""
    route: str
    active_item: NavigationRouteContract | None = Field(default=None)
    active_parent: NavigationRouteContract | None = Field(default=None)
    breadcrumb_chain: BreadcrumbChainContract
    navigation_state: NavigationStateContract
    guard_results: list[NavigationGuardResultContract] = Field(default_factory=list)
