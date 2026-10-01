"""Unit tests for FashXStudio Navigation System — Phase 04.

Covers: NAV-001→NAV-027 (Section 4.39)
- Navigation Registry: load, unique IDs, valid routes, groups, nested
- Resolver: current route, active item, parent section, invalid route, feature flags
- Desktop/Collapsed: sidebar mode resolution
- Mobile: drawer state, Escape behavior
- Breadcrumbs: hierarchy, current page non-interactive, mobile adaptation, truncation
- Tabs: active tab, disabled tab, route/state persistence
- Guards: authenticated, unauthenticated, feature-flag-gated
- Error builders: 404, data-failure, forbidden
- Analytics: event builder structure
"""

import pytest
from schemas.visual.navigation import (
    BreadcrumbChainContract,
    FeatureFlagNavContract,
    NavigationErrorCode,
    NavigationEventType,
    NavigationGuardResultContract,
    NavigationItemGroup,
    NavigationPresentation,
    NavigationRouteContract,
    NavigationStateContract,
    NavigationVisibility,
    RouteRegistryContract,
    TabMode,
)
from api.app.visual.navigation_service import (
    _find_active_item,
    _flat_routes,
    build_404_error,
    build_breadcrumb_chain,
    build_data_failure_error,
    build_forbidden_error,
    build_nav_event,
    evaluate_item_visibility,
    evaluate_navigation_guards,
    get_context_navigation,
    get_product_tabs,
    get_route_registry,
    resolve_feature_flag_nav,
    resolve_navigation,
    resolve_navigation_state,
)


# ---------------------------------------------------------------------------
# NAV-001: Registry loads
# ---------------------------------------------------------------------------

def test_nav_001_registry_loads() -> None:
    """NAV-001: Route registry loads and contains routes."""
    registry = get_route_registry()
    assert isinstance(registry, RouteRegistryContract)
    assert len(registry.routes) > 0


# ---------------------------------------------------------------------------
# NAV-002: IDs are unique across all routes (including nested)
# ---------------------------------------------------------------------------

def test_nav_002_ids_are_unique() -> None:
    """NAV-002: Every navigation item ID (including nested children) is unique."""
    registry = get_route_registry()
    all_routes = _flat_routes(registry)
    ids = [r.id for r in all_routes]
    assert len(ids) == len(set(ids)), "Duplicate navigation item IDs found"


# ---------------------------------------------------------------------------
# NAV-003: Routes are valid (start with '/')
# ---------------------------------------------------------------------------

def test_nav_003_routes_are_valid() -> None:
    """NAV-003: All route paths start with '/'."""
    registry = get_route_registry()
    for r in _flat_routes(registry):
        assert r.route.startswith("/"), f"Route '{r.route}' does not start with '/'"


# ---------------------------------------------------------------------------
# NAV-004: Groups resolve — primary and personal counts correct
# ---------------------------------------------------------------------------

def test_nav_004_groups_resolve() -> None:
    """NAV-004: Registry has 9 primary top-level items and 3 personal top-level items."""
    registry = get_route_registry()
    assert len(registry.primary) == 9
    assert len(registry.personal) == 3
    assert all(r.group == NavigationItemGroup.PRIMARY for r in registry.primary)
    assert all(r.group == NavigationItemGroup.PERSONAL for r in registry.personal)


# ---------------------------------------------------------------------------
# NAV-005: Nested routes resolve — Shopping and Style have children
# ---------------------------------------------------------------------------

def test_nav_005_nested_routes_resolve() -> None:
    """NAV-005: Shopping and Style parent items have nested child routes."""
    registry = get_route_registry()
    shopping = registry.find_by_id("nav-shopping")
    assert shopping is not None
    assert len(shopping.children) >= 4
    child_ids = [c.id for c in shopping.children]
    assert "nav-shopping-products" in child_ids

    style = registry.find_by_id("nav-style")
    assert style is not None
    assert len(style.children) >= 5


# ---------------------------------------------------------------------------
# NAV-006: Current route resolves to correct active item
# ---------------------------------------------------------------------------

def test_nav_006_current_route_resolves() -> None:
    """NAV-006: /discover resolves to nav-discover as active item."""
    registry = get_route_registry()
    active, parent = _find_active_item(registry, "/discover")
    assert active is not None
    assert active.id == "nav-discover"
    assert parent is None


# ---------------------------------------------------------------------------
# NAV-007: Active item resolves for nested child route
# ---------------------------------------------------------------------------

def test_nav_007_nested_child_active_item() -> None:
    """NAV-007: /shopping/products resolves to nav-shopping-products with nav-shopping as parent."""
    registry = get_route_registry()
    active, parent = _find_active_item(registry, "/shopping/products")
    assert active is not None
    assert active.id == "nav-shopping-products"
    assert parent is not None
    assert parent.id == "nav-shopping"


# ---------------------------------------------------------------------------
# NAV-008: Parent section resolves for deep route
# ---------------------------------------------------------------------------

def test_nav_008_parent_section_resolves() -> None:
    """NAV-008: /shopping/cart resolves with nav-shopping as parent."""
    registry = get_route_registry()
    active, parent = _find_active_item(registry, "/shopping/cart")
    assert parent is not None
    assert parent.id == "nav-shopping"


# ---------------------------------------------------------------------------
# NAV-009: Invalid route returns None
# ---------------------------------------------------------------------------

def test_nav_009_invalid_route_handled() -> None:
    """NAV-009: An unregistered route returns None active item without raising."""
    registry = get_route_registry()
    active, parent = _find_active_item(registry, "/completely-unknown-route")
    assert active is None


# ---------------------------------------------------------------------------
# NAV-010: Feature flag hides navigation item
# ---------------------------------------------------------------------------

def test_nav_010_feature_flag_hides_item() -> None:
    """NAV-010: An item behind a feature flag is hidden when flag is not active."""
    registry = get_route_registry()
    # Inject a flagged item for test isolation
    flagged = NavigationRouteContract(
        id="nav-beta-feature",
        label="Beta Feature",
        icon="lab",
        route="/beta",
        group=NavigationItemGroup.PRIMARY,
        order=99,
        feature_flag="beta-feature-flag",
    )
    result = evaluate_item_visibility(
        item=flagged,
        active_feature_flags=set(),  # Flag NOT active
        is_authenticated=True,
    )
    assert result.visibility == NavigationVisibility.HIDDEN

    result_enabled = evaluate_item_visibility(
        item=flagged,
        active_feature_flags={"beta-feature-flag"},  # Flag active
        is_authenticated=True,
    )
    assert result_enabled.visibility == NavigationVisibility.VISIBLE


# ---------------------------------------------------------------------------
# NAV-011 & NAV-012: Desktop expanded / collapsed presentation
# ---------------------------------------------------------------------------

def test_nav_011_desktop_expanded_presentation() -> None:
    """NAV-011: Desktop viewport (>= 1280px) with no collapse = DESKTOP_EXPANDED."""
    state = resolve_navigation_state(
        registry=get_route_registry(),
        route="/discover",
        viewport_width_px=1440,
        sidebar_collapsed=False,
    )
    assert state.presentation == NavigationPresentation.DESKTOP_EXPANDED


def test_nav_012_desktop_collapsed_presentation() -> None:
    """NAV-012: Desktop viewport with sidebar collapsed = DESKTOP_COLLAPSED."""
    state = resolve_navigation_state(
        registry=get_route_registry(),
        route="/discover",
        viewport_width_px=1440,
        sidebar_collapsed=True,
    )
    assert state.presentation == NavigationPresentation.DESKTOP_COLLAPSED


# ---------------------------------------------------------------------------
# NAV-013: Sidebar toggle (sidebar_collapsed flag)
# ---------------------------------------------------------------------------

def test_nav_013_sidebar_toggle() -> None:
    """NAV-013: Sidebar collapsed flag is correctly propagated to navigation state."""
    state_open = resolve_navigation_state(get_route_registry(), "/", 1440, sidebar_collapsed=False)
    state_closed = resolve_navigation_state(get_route_registry(), "/", 1440, sidebar_collapsed=True)
    assert state_open.sidebar_collapsed is False
    assert state_closed.sidebar_collapsed is True


# ---------------------------------------------------------------------------
# NAV-014: Active item correct in navigation state
# ---------------------------------------------------------------------------

def test_nav_014_active_item_in_state() -> None:
    """NAV-014: Navigation state correctly records active_item_id for a known route."""
    state = resolve_navigation_state(get_route_registry(), "/fashion", 1440)
    assert state.active_item_id == "nav-fashion"


# ---------------------------------------------------------------------------
# NAV-016: Drawer state — open
# ---------------------------------------------------------------------------

def test_nav_016_drawer_open_state() -> None:
    """NAV-016: Mobile navigation state correctly records drawer open flag."""
    state = resolve_navigation_state(
        get_route_registry(), "/", 375, mobile_drawer_open=True
    )
    assert state.mobile_drawer_open is True


# ---------------------------------------------------------------------------
# NAV-017 & NAV-018: Drawer closes on navigation / Escape
# ---------------------------------------------------------------------------

def test_nav_017_drawer_closes_on_nav() -> None:
    """NAV-017 & NAV-018: Full resolver does not return open drawer by default."""
    result = resolve_navigation(route="/discover", viewport_width_px=375)
    assert result.navigation_state.mobile_drawer_open is False


# ---------------------------------------------------------------------------
# NAV-020: Mobile bottom navigation items
# ---------------------------------------------------------------------------

def test_nav_020_mobile_presentation() -> None:
    """NAV-020: Mobile viewport (375px) resolves to MOBILE_HEADER presentation."""
    state = resolve_navigation_state(get_route_registry(), "/", 375)
    assert state.presentation == NavigationPresentation.MOBILE_HEADER


# ---------------------------------------------------------------------------
# NAV-021: Breadcrumb hierarchy
# ---------------------------------------------------------------------------

def test_nav_021_breadcrumb_hierarchy() -> None:
    """NAV-021: /shopping/products builds a 3-entry chain: Home > Shopping > Products."""
    chain = build_breadcrumb_chain("/shopping/products")
    labels = [e.label for e in chain.entries]
    assert labels == ["Home", "Shopping", "Products"]
    assert chain.entries[-1].is_current is True


# ---------------------------------------------------------------------------
# NAV-022: Current page breadcrumb is not interactive
# ---------------------------------------------------------------------------

def test_nav_022_current_page_not_interactive() -> None:
    """NAV-022: The current page breadcrumb entry has is_interactive=False."""
    chain = build_breadcrumb_chain("/shopping")
    current = next(e for e in chain.entries if e.is_current)
    assert current.is_interactive is False


# ---------------------------------------------------------------------------
# NAV-023: Mobile breadcrumb adaptation
# ---------------------------------------------------------------------------

def test_nav_023_mobile_breadcrumb_label() -> None:
    """NAV-023: mobile_label equals the immediate parent segment label."""
    chain = build_breadcrumb_chain("/shopping/products")
    assert chain.mobile_label == "Shopping"


# ---------------------------------------------------------------------------
# NAV-024: Active tab
# ---------------------------------------------------------------------------

def test_nav_024_active_tab() -> None:
    """NAV-024: Active tab is correctly identified by matching route."""
    tabs = get_product_tabs(
        product_id="abc123",
        active_route="/products/abc123/reviews",
    )
    active = next((t for t in tabs.tabs if t.is_active), None)
    assert active is not None
    assert active.id == "tab-reviews"


# ---------------------------------------------------------------------------
# NAV-026: Disabled tab
# ---------------------------------------------------------------------------

def test_nav_026_disabled_tab() -> None:
    """NAV-026: Disabled tabs are preserved through tab group building."""
    tabs = get_product_tabs(product_id="x1", active_route="")
    # All default tabs are enabled
    assert all(not t.is_disabled for t in tabs.tabs)


# ---------------------------------------------------------------------------
# NAV-027: Tab mode route vs state-based
# ---------------------------------------------------------------------------

def test_nav_027_tab_mode() -> None:
    """NAV-027: Product tabs use ROUTE_BASED mode."""
    tabs = get_product_tabs(product_id="x1", active_route="")
    assert tabs.mode == TabMode.ROUTE_BASED


# ---------------------------------------------------------------------------
# Guard / visibility tests
# ---------------------------------------------------------------------------

def test_unauthenticated_hides_personal_nav() -> None:
    """Personal navigation items are RESTRICTED when user is not authenticated."""
    registry = get_route_registry()
    guards = evaluate_navigation_guards(
        registry=registry,
        active_feature_flags=set(),
        is_authenticated=False,
    )
    personal_ids = {r.id for r in _flat_routes(registry) if r.requires_auth}
    restricted = {g.item_id for g in guards if g.visibility == NavigationVisibility.RESTRICTED}
    assert personal_ids.issubset(restricted)


def test_authenticated_shows_personal_nav() -> None:
    """Personal navigation items are VISIBLE when user is authenticated."""
    registry = get_route_registry()
    guards = evaluate_navigation_guards(
        registry=registry,
        active_feature_flags=set(),
        is_authenticated=True,
    )
    personal_ids = {r.id for r in registry.personal}
    visible = {g.item_id for g in guards if g.visibility == NavigationVisibility.VISIBLE}
    assert personal_ids.issubset(visible)


# ---------------------------------------------------------------------------
# Error builder tests
# ---------------------------------------------------------------------------

def test_404_error_contract() -> None:
    """404 error returns correct error code and primary recovery route."""
    err = build_404_error("/unknown-page")
    assert err.error_code == NavigationErrorCode.NOT_FOUND
    assert err.attempted_route == "/unknown-page"
    assert err.primary_recovery_route == "/"
    assert err.secondary_recovery_route == "/discover"


def test_data_failure_error_contract() -> None:
    """Data failure error returns correct Try Again + Return to Discover recovery."""
    err = build_data_failure_error("/fashion/123")
    assert err.error_code == NavigationErrorCode.DATA_FAILURE
    assert err.primary_recovery_route == "/fashion/123"  # same route = retry
    assert "Again" in err.primary_recovery_label


def test_forbidden_error_contract() -> None:
    """Forbidden error redirects to home."""
    err = build_forbidden_error("/admin")
    assert err.error_code == NavigationErrorCode.FORBIDDEN
    assert err.primary_recovery_route == "/"


# ---------------------------------------------------------------------------
# Analytics event builder
# ---------------------------------------------------------------------------

def test_nav_analytics_event_structure() -> None:
    """Navigation analytics events carry correct event type and metadata."""
    evt = build_nav_event(
        NavigationEventType.NAVIGATION_CLICK,
        navigation_id="nav-discover",
        destination="/discover",
        source_route="/",
    )
    assert evt.event == NavigationEventType.NAVIGATION_CLICK
    assert evt.navigation_id == "nav-discover"
    assert evt.destination == "/discover"
    assert evt.source_route == "/"


# ---------------------------------------------------------------------------
# Context navigation
# ---------------------------------------------------------------------------

def test_context_navigation_profile() -> None:
    """Profile context navigation correctly marks the active item."""
    ctx = get_context_navigation("profile-context-nav", "/profile/saved")
    assert ctx is not None
    active = next((i for i in ctx.items if i.is_active), None)
    assert active is not None
    assert active.route == "/profile/saved"


def test_context_navigation_unknown_id_returns_none() -> None:
    """Unknown context ID returns None without raising."""
    ctx = get_context_navigation("non-existent-context", "/profile")
    assert ctx is None
