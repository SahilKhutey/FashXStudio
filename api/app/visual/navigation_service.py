"""Navigation Service — Phase 04.

Provides the canonical FashXStudio route registry, navigation resolver,
breadcrumb chain builder, navigation state factory, tab group factory,
context navigation builder, navigation analytics event builder,
navigation guard/visibility evaluator, and error state builders.

Implements the unified navigation model from Section 4.2 (Rule 01–03):
  - One registry for all platforms (desktop/tablet/mobile)
  - Route is the source of location state
  - UI visibility ≠ authorization
"""

from schemas.visual.navigation import (
    BreadcrumbChainContract,
    BreadcrumbEntryContract,
    ContextNavItemContract,
    ContextNavigationContract,
    FeatureFlagNavContract,
    NavigationAnalyticsEventContract,
    NavigationErrorCode,
    NavigationErrorContract,
    NavigationEventType,
    NavigationGuardResultContract,
    NavigationItemGroup,
    NavigationPresentation,
    NavigationResolverResultContract,
    NavigationRouteContract,
    NavigationStateContract,
    NavigationVisibility,
    NestedNavExpansion,
    RouteRegistryContract,
    TabContract,
    TabGroupContract,
    TabMode,
)


# ---------------------------------------------------------------------------
# 1. Canonical Route Registry (Section 4.3 & 4.4)
# ---------------------------------------------------------------------------

def _route(
    route_id: str,
    label: str,
    icon: str,
    route: str,
    group: NavigationItemGroup,
    order: int,
    requires_auth: bool = False,
    active_match: list[str] | None = None,
    feature_flag: str | None = None,
    children: list[NavigationRouteContract] | None = None,
) -> NavigationRouteContract:
    return NavigationRouteContract(
        id=route_id,
        label=label,
        icon=icon,
        route=route,
        group=group,
        order=order,
        requires_auth=requires_auth,
        active_match=active_match or [],
        feature_flag=feature_flag,
        children=children or [],
    )


P = NavigationItemGroup.PRIMARY
PERS = NavigationItemGroup.PERSONAL

_ROUTE_REGISTRY = RouteRegistryContract(
    routes=[
        # PRIMARY
        _route("nav-home",     "Home",     "home",     "/",         P,    1, active_match=["/(tabs)/discover"]),
        _route("nav-discover", "Discover", "compass",  "/discover", P,    2, active_match=["/discover/"]),
        _route("nav-search",   "Search",   "search",   "/search",   P,    3),
        _route("nav-fashion",  "Fashion",  "sparkles", "/fashion",  P,    4, active_match=["/fashion/"]),
        _route("nav-shopping", "Shopping", "bag",      "/shopping", P,    5,
               active_match=["/shopping/"],
               children=[
                   _route("nav-shopping-products",  "All Products", "grid",     "/shopping/products",  P, 1),
                   _route("nav-shopping-categories","Categories",   "layers",   "/shopping/categories",P, 2),
                   _route("nav-shopping-cart",      "Cart",         "cart",     "/shopping/cart",      P, 3, requires_auth=True),
                   _route("nav-shopping-orders",    "Orders",       "box",      "/shopping/orders",    P, 4, requires_auth=True),
               ]),
        _route("nav-style",    "Style",    "wand",     "/style",    P,    6,
               active_match=["/style/"],
               children=[
                   _route("nav-style-home",     "Style Home",    "home",     "/style",             P, 1),
                   _route("nav-style-outfits",  "Outfit Builder","tool",     "/style/outfits",     P, 2),
                   _route("nav-style-looks",    "Look Builder",  "image",    "/style/looks",       P, 3),
                   _route("nav-style-saved",    "Saved Looks",   "bookmark", "/style/saved",       P, 4, requires_auth=True),
                   _route("nav-style-prefs",    "Preferences",   "sliders",  "/style/preferences", P, 5, requires_auth=True),
               ]),
        _route("nav-trends",   "Trends",   "trending", "/trends",   P,    7, active_match=["/trends/"]),
        _route("nav-maps",     "Maps",     "map",      "/maps",     P,    8, active_match=["/maps/"]),
        _route("nav-ai",       "AI",       "cpu",      "/ai",       P,    9, active_match=["/ai/"]),
        # PERSONAL
        _route("nav-saved",    "Saved",    "bookmark", "/saved",    PERS, 1, requires_auth=True),
        _route("nav-wishlist", "Wishlist", "heart",    "/wishlist", PERS, 2, requires_auth=True),
        _route("nav-profile",  "Profile",  "person",   "/profile",  PERS, 3, requires_auth=True,
               children=[
                   _route("nav-profile-overview", "Overview",    "user",    "/profile",              PERS, 1, requires_auth=True),
                   _route("nav-profile-saved",    "Saved",       "bookmark","/profile/saved",        PERS, 2, requires_auth=True),
                   _route("nav-profile-wishlist", "Wishlist",    "heart",   "/profile/wishlist",     PERS, 3, requires_auth=True),
                   _route("nav-profile-prefs",    "Preferences", "sliders", "/profile/preferences",  PERS, 4, requires_auth=True),
                   _route("nav-profile-settings", "Settings",    "settings","/profile/settings",     PERS, 5, requires_auth=True),
               ]),
    ]
)


def get_route_registry() -> RouteRegistryContract:
    """Return the canonical FashXStudio route registry (Section 4.3)."""
    return _ROUTE_REGISTRY


# ---------------------------------------------------------------------------
# 2. Navigation Resolver (Section 4.1 & 4.2)
# ---------------------------------------------------------------------------

def _flat_routes(registry: RouteRegistryContract) -> list[NavigationRouteContract]:
    """Return all routes including nested children as a flat list."""
    flat: list[NavigationRouteContract] = []
    for r in registry.routes:
        flat.append(r)
        flat.extend(r.children)
    return flat


def _find_active_item(
    registry: RouteRegistryContract,
    route: str,
) -> tuple[NavigationRouteContract | None, NavigationRouteContract | None]:
    """Return (active_item, active_parent) for a given route path."""
    for parent_route in registry.routes:
        if parent_route.route == route or route in parent_route.active_match:
            return parent_route, None
        if route.startswith(parent_route.route.rstrip("/") + "/") and parent_route.route != "/":
            for child in parent_route.children:
                if child.route == route or route in child.active_match:
                    return child, parent_route
            # No exact child match — the parent is still the "active" section
            return None, parent_route
        for child in parent_route.children:
            if child.route == route or route in child.active_match:
                return child, parent_route
    return None, None


# ---------------------------------------------------------------------------
# 3. Breadcrumb Builder (Section 4.14 & 4.15)
# ---------------------------------------------------------------------------

_ROUTE_LABELS: dict[str, str] = {
    "/": "Home",
    "/discover": "Discover",
    "/search": "Search",
    "/fashion": "Fashion",
    "/shopping": "Shopping",
    "/shopping/products": "Products",
    "/shopping/categories": "Categories",
    "/shopping/cart": "Cart",
    "/shopping/orders": "Orders",
    "/style": "Style",
    "/style/outfits": "Outfit Builder",
    "/style/looks": "Look Builder",
    "/style/saved": "Saved Looks",
    "/style/preferences": "Preferences",
    "/trends": "Trends",
    "/maps": "Maps",
    "/ai": "AI",
    "/saved": "Saved",
    "/wishlist": "Wishlist",
    "/profile": "Profile",
    "/profile/saved": "Saved",
    "/profile/wishlist": "Wishlist",
    "/profile/preferences": "Preferences",
    "/profile/settings": "Settings",
}


def build_breadcrumb_chain(pathname: str) -> BreadcrumbChainContract:
    """Build a typed breadcrumb chain from a URL pathname (Section 4.14 & 4.15)."""
    if pathname == "/" or not pathname:
        return BreadcrumbChainContract(
            entries=[
                BreadcrumbEntryContract(
                    label="Home", route="/", position=1, is_current=True, is_interactive=False,
                )
            ],
            mobile_label="Home",
            is_truncated=False,
        )

    segments = [s for s in pathname.split("/") if s]
    entries: list[BreadcrumbEntryContract] = [
        BreadcrumbEntryContract(label="Home", route="/", position=1, is_current=False, is_interactive=True)
    ]

    current_path = ""
    for idx, segment in enumerate(segments):
        current_path += f"/{segment}"
        label = _ROUTE_LABELS.get(current_path, segment.replace("-", " ").title())
        is_last = idx == len(segments) - 1
        entries.append(
            BreadcrumbEntryContract(
                label=label,
                route=current_path,
                position=idx + 2,
                is_current=is_last,
                is_interactive=not is_last,
            )
        )

    # Deep hierarchy truncation: collapse middle entries if > 4 levels (Section 4.15)
    is_truncated = len(entries) > 4
    mobile_label = entries[-2].label if len(entries) >= 2 else "Home"

    return BreadcrumbChainContract(
        entries=entries,
        mobile_label=mobile_label,
        is_truncated=is_truncated,
    )


# ---------------------------------------------------------------------------
# 4. Navigation State Builder (Section 4.37)
# ---------------------------------------------------------------------------

def resolve_navigation_state(
    registry: RouteRegistryContract,
    route: str,
    viewport_width_px: int = 375,
    sidebar_collapsed: bool = False,
    mobile_drawer_open: bool = False,
    navigation_history: list[str] | None = None,
) -> NavigationStateContract:
    """Build a fully resolved NavigationStateContract for a route + viewport."""
    from api.app.visual.shell_service import resolve_shell_layout_mode
    from schemas.visual.shell import ShellLayoutMode

    active_item, active_parent = _find_active_item(registry, route)
    layout_mode = resolve_shell_layout_mode(viewport_width_px)

    presentation_map = {
        ShellLayoutMode.DESKTOP: (
            NavigationPresentation.DESKTOP_COLLAPSED if sidebar_collapsed
            else NavigationPresentation.DESKTOP_EXPANDED
        ),
        ShellLayoutMode.TABLET: NavigationPresentation.TABLET,
        ShellLayoutMode.MOBILE: NavigationPresentation.MOBILE_HEADER,
    }
    presentation = presentation_map.get(layout_mode, NavigationPresentation.MOBILE_HEADER)

    expanded_group_ids: list[str] = []
    if active_parent:
        expanded_group_ids.append(active_parent.id)
    elif active_item and active_item.children:
        expanded_group_ids.append(active_item.id)

    history = (navigation_history or [])[-20:]  # cap at 20

    return NavigationStateContract(
        current_route=route,
        active_item_id=active_item.id if active_item else None,
        active_parent_id=active_parent.id if active_parent else None,
        expanded_group_ids=expanded_group_ids,
        mobile_drawer_open=mobile_drawer_open,
        sidebar_collapsed=sidebar_collapsed,
        focused_item_id=None,
        presentation=presentation,
        navigation_history=history,
    )


# ---------------------------------------------------------------------------
# 5. Navigation Resolver (Section 4.1)
# ---------------------------------------------------------------------------

def resolve_navigation(
    route: str,
    viewport_width_px: int = 375,
    active_feature_flags: set[str] | None = None,
    is_authenticated: bool = False,
    sidebar_collapsed: bool = False,
) -> NavigationResolverResultContract:
    """Full navigation resolution for a route (Section 4.1)."""
    registry = get_route_registry()
    active_item, active_parent = _find_active_item(registry, route)
    breadcrumb_chain = build_breadcrumb_chain(route)
    nav_state = resolve_navigation_state(
        registry=registry,
        route=route,
        viewport_width_px=viewport_width_px,
        sidebar_collapsed=sidebar_collapsed,
    )

    # Build guard results for all items
    guard_results = evaluate_navigation_guards(
        registry=registry,
        active_feature_flags=active_feature_flags or set(),
        is_authenticated=is_authenticated,
    )

    return NavigationResolverResultContract(
        route=route,
        active_item=active_item,
        active_parent=active_parent,
        breadcrumb_chain=breadcrumb_chain,
        navigation_state=nav_state,
        guard_results=guard_results,
    )


# ---------------------------------------------------------------------------
# 6. Navigation Guards / Visibility (Section 4.28 & 4.29)
# ---------------------------------------------------------------------------

def evaluate_item_visibility(
    item: NavigationRouteContract,
    active_feature_flags: set[str],
    is_authenticated: bool,
) -> NavigationGuardResultContract:
    """Evaluate visibility for a single navigation item (Section 4.28 Rule 03)."""
    if item.feature_flag and item.feature_flag not in active_feature_flags:
        return NavigationGuardResultContract(
            item_id=item.id,
            visibility=NavigationVisibility.HIDDEN,
            reason=f"Feature flag '{item.feature_flag}' is not enabled",
        )
    if item.requires_auth and not is_authenticated:
        return NavigationGuardResultContract(
            item_id=item.id,
            visibility=NavigationVisibility.RESTRICTED,
            reason="Authentication required",
            redirect_route="/auth/login",
        )
    return NavigationGuardResultContract(
        item_id=item.id,
        visibility=item.visibility,
    )


def evaluate_navigation_guards(
    registry: RouteRegistryContract,
    active_feature_flags: set[str],
    is_authenticated: bool,
) -> list[NavigationGuardResultContract]:
    """Evaluate visibility for every item in the registry (Section 4.28)."""
    results: list[NavigationGuardResultContract] = []
    for item in _flat_routes(registry):
        results.append(
            evaluate_item_visibility(item, active_feature_flags, is_authenticated)
        )
    return results


def resolve_feature_flag_nav(
    item: NavigationRouteContract,
    active_feature_flags: set[str],
) -> FeatureFlagNavContract:
    """Resolve a feature-flag-gated navigation item (Section 4.29)."""
    if not item.feature_flag:
        return FeatureFlagNavContract(
            flag_key="",
            is_enabled=True,
            item_id=item.id,
            resolved_visibility=item.visibility,
        )
    is_enabled = item.feature_flag in active_feature_flags
    return FeatureFlagNavContract(
        flag_key=item.feature_flag,
        is_enabled=is_enabled,
        item_id=item.id,
        resolved_visibility=NavigationVisibility.VISIBLE if is_enabled else NavigationVisibility.HIDDEN,
    )


# ---------------------------------------------------------------------------
# 7. Tab Group Builders (Section 4.16–4.18)
# ---------------------------------------------------------------------------

PRODUCT_TABS = TabGroupContract(
    group_id="product-detail-tabs",
    label="Product details",
    mode=TabMode.ROUTE_BASED,
    tabs=[
        TabContract(id="tab-overview",     label="Overview",   route="/products/{id}",               is_active=True,  is_disabled=False),
        TabContract(id="tab-reviews",      label="Reviews",    route="/products/{id}/reviews",       is_active=False, is_disabled=False),
        TabContract(id="tab-specs",        label="Specs",      route="/products/{id}/specifications",is_active=False, is_disabled=False),
        TabContract(id="tab-styling",      label="Styling",    route="/products/{id}/styling",       is_active=False, is_disabled=False),
    ],
)

PROFILE_CONTEXT_NAV = ContextNavigationContract(
    context_id="profile-context-nav",
    label="Profile navigation",
    mode=TabMode.ROUTE_BASED,
    items=[
        ContextNavItemContract(id="ctx-profile-overview", label="Overview",    route="/profile",             is_active=True,  is_disabled=False),
        ContextNavItemContract(id="ctx-profile-saved",    label="Saved",       route="/profile/saved",       is_active=False, is_disabled=False),
        ContextNavItemContract(id="ctx-profile-wishlist", label="Wishlist",    route="/profile/wishlist",    is_active=False, is_disabled=False),
        ContextNavItemContract(id="ctx-profile-prefs",    label="Preferences", route="/profile/preferences", is_active=False, is_disabled=False),
        ContextNavItemContract(id="ctx-profile-settings", label="Settings",    route="/profile/settings",    is_active=False, is_disabled=False),
    ],
)


def get_product_tabs(active_route: str, product_id: str) -> TabGroupContract:
    """Build product detail tab group with correct active state."""
    tabs = []
    for tab in PRODUCT_TABS.tabs:
        resolved_route = tab.route.replace("{id}", product_id) if tab.route else None
        tabs.append(TabContract(
            id=tab.id,
            label=tab.label,
            route=resolved_route,
            is_active=resolved_route == active_route,
            is_disabled=tab.is_disabled,
        ))
    return TabGroupContract(
        group_id=PRODUCT_TABS.group_id,
        label=PRODUCT_TABS.label,
        mode=PRODUCT_TABS.mode,
        tabs=tabs,
    )


def get_context_navigation(context_id: str, active_route: str) -> ContextNavigationContract | None:
    """Return context navigation for a given context id with active state applied."""
    context_map: dict[str, ContextNavigationContract] = {
        "profile-context-nav": PROFILE_CONTEXT_NAV,
    }
    ctx = context_map.get(context_id)
    if not ctx:
        return None
    items = [
        ContextNavItemContract(
            id=item.id,
            label=item.label,
            route=item.route,
            is_active=item.route == active_route,
            is_disabled=item.is_disabled,
        )
        for item in ctx.items
    ]
    return ContextNavigationContract(
        context_id=ctx.context_id,
        label=ctx.label,
        mode=ctx.mode,
        items=items,
    )


# ---------------------------------------------------------------------------
# 8. Analytics Event Builder (Section 4.30)
# ---------------------------------------------------------------------------

def build_nav_event(
    event_type: NavigationEventType,
    navigation_id: str | None = None,
    destination: str | None = None,
    source_route: str | None = None,
    label: str | None = None,
    metadata: dict | None = None,
) -> NavigationAnalyticsEventContract:
    """Build a structured navigation analytics event (Section 4.30)."""
    return NavigationAnalyticsEventContract(
        event=event_type,
        navigation_id=navigation_id,
        destination=destination,
        source_route=source_route,
        label=label,
        metadata=metadata or {},
    )


# ---------------------------------------------------------------------------
# 9. Navigation Error Builders (Section 4.26 & 4.27)
# ---------------------------------------------------------------------------

def build_404_error(attempted_route: str) -> NavigationErrorContract:
    """Build a 404 navigation error contract (Section 4.27)."""
    return NavigationErrorContract(
        error_code=NavigationErrorCode.NOT_FOUND,
        attempted_route=attempted_route,
        user_message="Page not found.",
        primary_recovery_route="/",
        primary_recovery_label="Go Home",
        secondary_recovery_route="/discover",
        secondary_recovery_label="Explore Discover",
    )


def build_data_failure_error(attempted_route: str) -> NavigationErrorContract:
    """Build a data-failure navigation error contract (Section 4.26)."""
    return NavigationErrorContract(
        error_code=NavigationErrorCode.DATA_FAILURE,
        attempted_route=attempted_route,
        user_message="We couldn't load this page.",
        primary_recovery_route=attempted_route,
        primary_recovery_label="Try Again",
        secondary_recovery_route="/discover",
        secondary_recovery_label="Return to Discover",
    )


def build_forbidden_error(attempted_route: str) -> NavigationErrorContract:
    """Build a forbidden navigation error contract (Section 4.28)."""
    return NavigationErrorContract(
        error_code=NavigationErrorCode.FORBIDDEN,
        attempted_route=attempted_route,
        user_message="You don't have permission to view this page.",
        primary_recovery_route="/",
        primary_recovery_label="Go Home",
        secondary_recovery_route="/discover",
        secondary_recovery_label="Explore Discover",
    )
