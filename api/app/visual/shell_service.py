"""Application Shell Service — Phase 03.

Provides the canonical navigation configuration, shell layout resolution from breakpoint,
breadcrumb resolution, page header builders, overlay/toast management, and
layout template construction for the FashXStudio Application Shell.
Adheres to Rule I01 (Layer Separation) and Rule I02 (Contract Primacy).
"""

from schemas.visual.shell import (
    AppHeaderContract,
    ApplicationShellContract,
    BreadcrumbItemContract,
    ContentSectionContract,
    LayoutTemplate,
    LayoutTemplateContract,
    MobileDrawerState,
    NavigationConfigContract,
    NavigationGroup,
    NavigationItemContract,
    NavigationItemState,
    OverlayContract,
    OverlayRegistryContract,
    OverlayType,
    PageActionContract,
    PageContainerContract,
    PageHeaderContract,
    PageHeaderVariant,
    ShellLayoutMode,
    ShellLoadState,
    SidebarMode,
    ToastContract,
    ToastType,
)


# ---------------------------------------------------------------------------
# 1. Canonical Navigation Configuration (Section 3.10 & 3.14)
# ---------------------------------------------------------------------------

PRIMARY_NAV_ITEMS: list[NavigationItemContract] = [
    NavigationItemContract(id="nav-home",     label="Home",     icon="home",     route="/",              group=NavigationGroup.PRIMARY),
    NavigationItemContract(id="nav-discover", label="Discover", icon="compass",  route="/discover",      group=NavigationGroup.PRIMARY),
    NavigationItemContract(id="nav-search",   label="Search",   icon="search",   route="/search",        group=NavigationGroup.PRIMARY),
    NavigationItemContract(id="nav-fashion",  label="Fashion",  icon="sparkles", route="/fashion",       group=NavigationGroup.PRIMARY),
    NavigationItemContract(id="nav-shopping", label="Shopping", icon="bag",      route="/shopping",      group=NavigationGroup.PRIMARY),
    NavigationItemContract(id="nav-style",    label="Style",    icon="wand",     route="/style",         group=NavigationGroup.PRIMARY),
    NavigationItemContract(id="nav-trends",   label="Trends",   icon="trending", route="/trends",        group=NavigationGroup.PRIMARY),
    NavigationItemContract(id="nav-maps",     label="Maps",     icon="map",      route="/maps",          group=NavigationGroup.PRIMARY),
    NavigationItemContract(id="nav-ai",       label="AI",       icon="cpu",      route="/ai",            group=NavigationGroup.PRIMARY),
]

PERSONAL_NAV_ITEMS: list[NavigationItemContract] = [
    NavigationItemContract(id="nav-saved",    label="Saved",    icon="bookmark", route="/saved",         group=NavigationGroup.PERSONAL, requires_auth=True),
    NavigationItemContract(id="nav-wishlist", label="Wishlist", icon="heart",    route="/wishlist",      group=NavigationGroup.PERSONAL, requires_auth=True),
    NavigationItemContract(id="nav-profile",  label="Profile",  icon="person",   route="/profile",       group=NavigationGroup.PERSONAL, requires_auth=True),
]

# Mobile bottom bar uses exactly 5 slots: 4 primary + "Menu" menu trigger
BOTTOM_BAR_IDS: list[str] = ["nav-home", "nav-discover", "nav-style", "nav-saved", "nav-menu"]

_CANONICAL_NAV_CONFIG = NavigationConfigContract(
    primary=PRIMARY_NAV_ITEMS,
    personal=PERSONAL_NAV_ITEMS,
    bottom_bar_ids=["nav-home", "nav-discover", "nav-style", "nav-saved"],
)


def get_navigation_config() -> NavigationConfigContract:
    """Return the canonical navigation configuration."""
    return _CANONICAL_NAV_CONFIG


# ---------------------------------------------------------------------------
# 2. Shell Layout Mode Resolution from viewport width (Section 3.29)
# ---------------------------------------------------------------------------

def resolve_shell_layout_mode(viewport_width_px: int) -> ShellLayoutMode:
    """Resolve the appropriate shell layout mode from viewport width using Phase 02 breakpoints.

    Desktop (>= 1024px)  → Full sidebar + header + main
    Tablet (768–1023px)  → Compact/collapsible sidebar + header + main
    Mobile (<768px)      → Mobile header + main content + bottom navigation
    """
    if viewport_width_px >= 1024:
        return ShellLayoutMode.DESKTOP
    elif viewport_width_px >= 768:
        return ShellLayoutMode.TABLET
    return ShellLayoutMode.MOBILE


def resolve_sidebar_mode(viewport_width_px: int) -> SidebarMode:
    """Resolve sidebar expansion mode from viewport width."""
    if viewport_width_px >= 1280:
        return SidebarMode.EXPANDED
    elif viewport_width_px >= 1024:
        return SidebarMode.COLLAPSED
    return SidebarMode.HIDDEN


# ---------------------------------------------------------------------------
# 3. Breadcrumb Builder (Section 3.3 & 3.17)
# ---------------------------------------------------------------------------

_ROUTE_LABEL_MAP: dict[str, str] = {
    "/": "Home",
    "/discover": "Discover",
    "/search": "Search",
    "/fashion": "Fashion",
    "/shopping": "Shopping",
    "/style": "Style",
    "/trends": "Trends",
    "/maps": "Maps",
    "/ai": "AI",
    "/saved": "Saved",
    "/wishlist": "Wishlist",
    "/profile": "Profile",
}


def resolve_breadcrumbs(pathname: str) -> list[BreadcrumbItemContract]:
    """Resolve breadcrumb trail from a URL pathname (Section 3.17)."""
    if pathname == "/" or not pathname:
        return [BreadcrumbItemContract(label="Home", route="/", is_current=True)]

    breadcrumbs: list[BreadcrumbItemContract] = [
        BreadcrumbItemContract(label="Home", route="/", is_current=False),
    ]

    segments = [s for s in pathname.split("/") if s]
    current_path = ""
    for idx, segment in enumerate(segments):
        current_path += f"/{segment}"
        label = _ROUTE_LABEL_MAP.get(current_path, segment.replace("-", " ").title())
        breadcrumbs.append(
            BreadcrumbItemContract(
                label=label,
                route=current_path,
                is_current=idx == len(segments) - 1,
            )
        )

    return breadcrumbs


# ---------------------------------------------------------------------------
# 4. Page Header Builder (Section 3.17 & 3.18)
# ---------------------------------------------------------------------------

def build_page_header(
    title: str,
    variant: PageHeaderVariant = PageHeaderVariant.STANDARD,
    description: str | None = None,
    route: str = "/",
    primary_action: PageActionContract | None = None,
    secondary_actions: list[PageActionContract] | None = None,
    result_count: int | None = None,
    status_label: str | None = None,
    visual_uri: str | None = None,
) -> PageHeaderContract:
    """Factory for building typed page headers with automatic breadcrumb resolution."""
    return PageHeaderContract(
        variant=variant,
        title=title,
        description=description,
        breadcrumbs=resolve_breadcrumbs(route),
        primary_action=primary_action,
        secondary_actions=secondary_actions or [],
        status_label=status_label,
        result_count=result_count,
        visual_uri=visual_uri,
    )


# ---------------------------------------------------------------------------
# 5. Application Shell Factory (Section 3.33)
# ---------------------------------------------------------------------------

def build_application_shell(
    viewport_width_px: int = 375,
    active_route: str = "/",
    theme_mode: str = "light",
    notification_count: int = 0,
    load_state: ShellLoadState = ShellLoadState.READY,
) -> ApplicationShellContract:
    """Construct a fully resolved ApplicationShellContract for a given viewport and route."""
    layout_mode = resolve_shell_layout_mode(viewport_width_px)
    sidebar_mode = resolve_sidebar_mode(viewport_width_px)
    nav_config = get_navigation_config()

    # Mark the active navigation item
    all_items = nav_config.primary + nav_config.personal
    for item in all_items:
        object.__setattr__(
            item,
            "state",
            NavigationItemState.SELECTED if item.route == active_route else NavigationItemState.DEFAULT,
        )

    return ApplicationShellContract(
        navigation=nav_config,
        header=AppHeaderContract(
            notification_count=notification_count,
            show_search=True,
            show_notifications=True,
            show_user_menu=True,
            is_sticky=True,
        ),
        sidebar_mode=sidebar_mode,
        drawer_state=MobileDrawerState.CLOSED,
        layout_mode=layout_mode,
        load_state=load_state,
        active_route=active_route,
        theme_mode=theme_mode,
    )


# ---------------------------------------------------------------------------
# 6. Layout Template Builders (Section 3.31)
# ---------------------------------------------------------------------------

def build_layout_template(
    template: LayoutTemplate,
    page_header: PageHeaderContract | None = None,
    sections: list[ContentSectionContract] | None = None,
    max_width: str = "1280px",
) -> LayoutTemplateContract:
    """Build a typed layout template with optional page header and content sections."""
    full_bleed_templates = {
        LayoutTemplate.EDITORIAL,
        LayoutTemplate.MAP,
        LayoutTemplate.BUILDER,
    }
    return LayoutTemplateContract(
        template=template,
        page_header=page_header,
        container=PageContainerContract(max_width=max_width),
        sections=sections or [],
        is_full_bleed=template in full_bleed_templates,
        scroll_behavior="feature-local" if template == LayoutTemplate.MAP else "viewport",
    )


# ---------------------------------------------------------------------------
# 7. Overlay & Toast Service (Section 3.21 & 3.22)
# ---------------------------------------------------------------------------

def create_overlay(
    overlay_id: str,
    overlay_type: OverlayType,
    title: str | None = None,
    is_dismissible: bool = True,
    has_focus_trap: bool = True,
) -> OverlayContract:
    """Create a typed overlay contract entry."""
    return OverlayContract(
        overlay_id=overlay_id,
        overlay_type=overlay_type,
        title=title,
        is_dismissible=is_dismissible,
        has_focus_trap=has_focus_trap,
    )


def create_toast(
    toast_id: str,
    message: str,
    toast_type: ToastType = ToastType.INFO,
    action_label: str | None = None,
    auto_dismiss_ms: int = 4000,
    is_persistent: bool = False,
) -> ToastContract:
    """Create a typed toast notification entry."""
    return ToastContract(
        toast_id=toast_id,
        toast_type=toast_type,
        message=message,
        action_label=action_label,
        auto_dismiss_ms=auto_dismiss_ms,
        is_persistent=is_persistent,
    )


def push_toast(
    registry: OverlayRegistryContract,
    toast: ToastContract,
) -> OverlayRegistryContract:
    """Add a toast to the registry queue (returns new registry instance)."""
    return OverlayRegistryContract(
        active_overlays=registry.active_overlays,
        toast_queue=[*registry.toast_queue, toast],
    )


def dismiss_toast(
    registry: OverlayRegistryContract,
    toast_id: str,
) -> OverlayRegistryContract:
    """Remove a toast from the queue by ID (returns new registry instance)."""
    return OverlayRegistryContract(
        active_overlays=registry.active_overlays,
        toast_queue=[t for t in registry.toast_queue if t.toast_id != toast_id],
    )


def push_overlay(
    registry: OverlayRegistryContract,
    overlay: OverlayContract,
) -> OverlayRegistryContract:
    """Push an overlay on to the active stack (returns new registry instance)."""
    return OverlayRegistryContract(
        active_overlays=[*registry.active_overlays, overlay],
        toast_queue=registry.toast_queue,
    )


def pop_overlay(registry: OverlayRegistryContract) -> OverlayRegistryContract:
    """Pop the top overlay from the active stack (returns new registry instance)."""
    return OverlayRegistryContract(
        active_overlays=registry.active_overlays[:-1],
        toast_queue=registry.toast_queue,
    )
