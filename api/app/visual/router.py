"""FastAPI Router for FashXStudio Visual Layer Architecture & Design Tokens.

Exposes endpoints for Screen Inventory, Templates, Dependency Groups, Breakpoints, Domains,
and the Design Token System (Primitives, Semantic Themes, MST, Components, WCAG Validation).
Adheres to Rule I01 (Layer Separation) and Rule I19 (Standardized Error Envelopes).
"""

from typing import Any
from fastapi import APIRouter, HTTPException, Query, status

from api.app.core.errors import EntityNotFoundError
from schemas.visual.v1 import (
    BreakpointConfig,
    DeviceBreakpoint,
    ImplementationDependencyGroup,
    PageTemplateType,
    ScreenDefinition,
    ScreenDomain,
    ScreenInventoryRegistry,
)
from schemas.visual.tokens import (
    DesignTokenRegistry,
    MonkSkinTonePalette,
    ThemeMode,
    ThemeTokens,
    TokenValidationReport,
)
from .catalog import BREAKPOINT_CONFIGS, get_screen_inventory
from .tokens_service import (
    calculate_adaptive_columns,
    get_theme_tokens,
    get_token_registry,
    validate_tokens,
)
from schemas.visual.shell import (
    ApplicationShellContract,
    BreadcrumbItemContract,
    LayoutTemplate,
    LayoutTemplateContract,
    NavigationConfigContract,
    OverlayContract,
    OverlayRegistryContract,
    OverlayType,
    PageHeaderContract,
    PageHeaderVariant,
    ToastContract,
    ToastType,
)
from .shell_service import (
    build_application_shell,
    build_layout_template,
    build_page_header,
    create_overlay,
    create_toast,
    dismiss_toast,
    get_navigation_config,
    pop_overlay,
    push_overlay,
    push_toast,
    resolve_breadcrumbs,
    resolve_shell_layout_mode,
    resolve_sidebar_mode,
)

router = APIRouter(prefix="/visual", tags=["Visual Architecture"])


# ---------------------------------------------------------------------------
# Screen Inventory & Layout Architecture Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/screens",
    response_model=ScreenInventoryRegistry,
    summary="Get complete screen inventory",
)
def list_screens(
    domain: ScreenDomain | None = Query(default=None, description="Filter by domain"),
    template_type: PageTemplateType | None = Query(default=None, description="Filter by template"),
    dependency_group: ImplementationDependencyGroup | None = Query(default=None, description="Filter by group"),
    requires_auth: bool | None = Query(default=None, description="Filter by auth requirement"),
) -> ScreenInventoryRegistry:
    inventory = get_screen_inventory()
    filtered = inventory.screens
    if domain is not None:
        filtered = [s for s in filtered if s.domain == domain]
    if template_type is not None:
        filtered = [s for s in filtered if s.template_type == template_type]
    if dependency_group is not None:
        filtered = [s for s in filtered if s.dependency_group == dependency_group]
    if requires_auth is not None:
        filtered = [s for s in filtered if s.requires_auth == requires_auth]
    return ScreenInventoryRegistry(
        version=inventory.version,
        total_screens=len(filtered),
        screens=filtered,
    )


@router.get(
    "/screens/{screen_id}",
    response_model=ScreenDefinition,
    summary="Get screen details by ID or Code",
)
def get_screen(screen_id: str) -> ScreenDefinition:
    inventory = get_screen_inventory()
    screen = inventory.get_screen(screen_id)
    if screen is None:
        raise EntityNotFoundError("Screen", screen_id)
    return screen


@router.get(
    "/breakpoints",
    response_model=list[BreakpointConfig],
    summary="Get responsive device breakpoint configurations",
)
def list_breakpoints() -> list[BreakpointConfig]:
    return BREAKPOINT_CONFIGS


@router.get(
    "/domains",
    summary="Get domain summary",
)
def get_domain_summary() -> dict[str, int]:
    inventory = get_screen_inventory()
    summary: dict[str, int] = {}
    for screen in inventory.screens:
        summary[screen.domain] = summary.get(screen.domain, 0) + 1
    return summary


@router.get(
    "/templates",
    summary="Get screen count by page template",
)
def get_template_summary() -> dict[str, int]:
    inventory = get_screen_inventory()
    summary: dict[str, int] = {}
    for screen in inventory.screens:
        t = str(screen.template_type)
        summary[t] = summary.get(t, 0) + 1
    return summary


@router.get(
    "/dependency-groups",
    summary="Get screen count by dependency group",
)
def get_dependency_group_summary() -> dict[str, int]:
    inventory = get_screen_inventory()
    summary: dict[str, int] = {}
    for screen in inventory.screens:
        g = str(screen.dependency_group)
        summary[g] = summary.get(g, 0) + 1
    return summary


# ---------------------------------------------------------------------------
# Design Token System Endpoints (Phase 02)
# ---------------------------------------------------------------------------

@router.get(
    "/tokens",
    response_model=DesignTokenRegistry,
    summary="Get full design token registry",
)
def get_tokens() -> DesignTokenRegistry:
    """Return the frozen master design token registry containing all scales."""
    return get_token_registry()


@router.get(
    "/tokens/theme",
    response_model=ThemeTokens,
    summary="Get theme-resolved semantic tokens",
)
def get_theme(
    mode: ThemeMode = Query(default=ThemeMode.LIGHT, description="Theme mode (light or dark)"),
) -> ThemeTokens:
    """Resolve semantic surface, content, border, action, and status tokens for the given mode."""
    return get_theme_tokens(mode=mode)


@router.get(
    "/tokens/skin-tones",
    response_model=MonkSkinTonePalette,
    summary="Get Monk Skin Tone 10-point scale and undertones",
)
def get_skin_tones() -> MonkSkinTonePalette:
    """Return the Monk Skin Tone (MST) 10-point scale and undertone calibration values."""
    return get_token_registry().monk_skin_tones


@router.get(
    "/tokens/components/{component_name}",
    summary="Get component-specific token bindings",
)
def get_component_tokens(component_name: str) -> dict[str, Any]:
    """Retrieve pre-bound component tokens (e.g. product-card, fashion-card)."""
    registry = get_token_registry()
    name_clean = component_name.lower().replace("_", "-")
    if name_clean in ["product-card", "productcard"]:
        return registry.product_card_tokens.model_dump()
    elif name_clean in ["fashion-card", "fashioncard"]:
        return registry.fashion_card_tokens.model_dump()
    else:
        raise EntityNotFoundError("ComponentTokens", component_name)


@router.post(
    "/tokens/validate",
    response_model=TokenValidationReport,
    summary="Run automated token integrity and WCAG 2.2 contrast validation",
)
def run_token_validation() -> TokenValidationReport:
    """Execute WCAG 2.2 contrast calculations and check for broken token references."""
    return validate_tokens()


@router.get(
    "/tokens/grid-calculator",
    summary="Calculate adaptive grid columns based on container width",
)
def calculate_grid(
    container_width_px: int = Query(..., ge=1, description="Available container width in pixels"),
    min_card_width_px: int = Query(default=240, ge=50, description="Minimum card width in pixels"),
    gutter_px: int = Query(default=16, ge=0, description="Gutter spacing in pixels"),
    max_columns: int = Query(default=12, ge=1, le=24, description="Maximum allowed columns"),
) -> dict[str, int]:
    """Compute adaptive column count for dynamic product and fashion grids (Section 2.25)."""
    columns = calculate_adaptive_columns(
        container_width_px=container_width_px,
        min_card_width_px=min_card_width_px,
        gutter_px=gutter_px,
        max_columns=max_columns,
    )
    return {
        "container_width_px": container_width_px,
        "min_card_width_px": min_card_width_px,
        "gutter_px": gutter_px,
        "columns": columns,
    }


# ---------------------------------------------------------------------------
# Application Shell Endpoints (Phase 03)
# ---------------------------------------------------------------------------

@router.get(
    "/shell",
    response_model=ApplicationShellContract,
    summary="Get resolved application shell for a viewport and route",
)
def get_shell(
    viewport_width: int = Query(default=375, ge=1, description="Viewport width in pixels"),
    active_route: str = Query(default="/", description="Current active route path"),
    theme_mode: str = Query(default="light", description="Theme mode: light or dark"),
    notification_count: int = Query(default=0, ge=0, description="Notification badge count"),
) -> ApplicationShellContract:
    """Return a fully resolved application shell with navigation, layout mode, header, and sidebar."""
    return build_application_shell(
        viewport_width_px=viewport_width,
        active_route=active_route,
        theme_mode=theme_mode,
        notification_count=notification_count,
    )


@router.get(
    "/shell/navigation",
    response_model=NavigationConfigContract,
    summary="Get canonical application navigation configuration",
)
def get_navigation() -> NavigationConfigContract:
    """Return the full navigation configuration including primary, personal, and bottom bar items."""
    return get_navigation_config()


@router.get(
    "/shell/breadcrumbs",
    response_model=list[BreadcrumbItemContract],
    summary="Resolve breadcrumb trail for a route path",
)
def get_breadcrumbs(
    route: str = Query(..., description="Route path to resolve (e.g. /shopping/products/123)"),
) -> list[BreadcrumbItemContract]:
    """Resolve the breadcrumb trail from a URL pathname."""
    return resolve_breadcrumbs(route)


@router.get(
    "/shell/layout-mode",
    summary="Resolve shell layout mode from viewport width",
)
def get_layout_mode(
    viewport_width: int = Query(..., ge=1, description="Viewport width in pixels"),
) -> dict[str, str]:
    """Return the shell layout mode (desktop, tablet, mobile) and sidebar mode from viewport width."""
    layout_mode = resolve_shell_layout_mode(viewport_width)
    sidebar_mode = resolve_sidebar_mode(viewport_width)
    return {
        "viewport_width_px": str(viewport_width),
        "layout_mode": layout_mode.value,
        "sidebar_mode": sidebar_mode.value,
    }


@router.get(
    "/shell/page-header",
    response_model=PageHeaderContract,
    summary="Build a typed page header with automatic breadcrumb resolution",
)
def get_page_header(
    title: str = Query(..., description="Page title"),
    route: str = Query(default="/", description="Active route for breadcrumb resolution"),
    variant: PageHeaderVariant = Query(default=PageHeaderVariant.STANDARD),
    description: str | None = Query(default=None),
    result_count: int | None = Query(default=None),
) -> PageHeaderContract:
    """Generate a typed page header contract for a given route and variant."""
    return build_page_header(
        title=title,
        variant=variant,
        description=description,
        route=route,
        result_count=result_count,
    )


@router.get(
    "/shell/layout-template",
    response_model=LayoutTemplateContract,
    summary="Build a typed layout template specification",
)
def get_layout_template(
    template: LayoutTemplate = Query(..., description="Layout template type"),
    max_width: str = Query(default="1280px", description="Container max-width"),
) -> LayoutTemplateContract:
    """Return a layout template contract with container config and scroll behavior."""
    return build_layout_template(template=template, max_width=max_width)


# ---------------------------------------------------------------------------
# Navigation System Endpoints (Phase 04)
# ---------------------------------------------------------------------------

from schemas.visual.navigation import (
    BreadcrumbChainContract,
    ContextNavigationContract,
    FeatureFlagNavContract,
    NavigationAnalyticsEventContract,
    NavigationErrorContract,
    NavigationEventType,
    NavigationGuardResultContract,
    NavigationResolverResultContract,
    RouteRegistryContract,
    TabGroupContract,
)
from .navigation_service import (
    build_404_error,
    build_breadcrumb_chain,
    build_data_failure_error,
    build_forbidden_error,
    build_nav_event,
    evaluate_navigation_guards,
    get_context_navigation,
    get_product_tabs,
    get_route_registry,
    resolve_navigation,
    resolve_feature_flag_nav,
    PROFILE_CONTEXT_NAV,
)


@router.get(
    "/navigation/registry",
    response_model=RouteRegistryContract,
    summary="Get the canonical FashXStudio route registry",
)
def get_nav_registry() -> RouteRegistryContract:
    """Return the complete navigation route registry (primary + personal with nested children)."""
    return get_route_registry()


@router.get(
    "/navigation/resolve",
    response_model=NavigationResolverResultContract,
    summary="Resolve navigation state for a route + viewport",
)
def resolve_nav(
    route: str = Query(default="/", description="Route path to resolve"),
    viewport_width: int = Query(default=375, ge=1, description="Viewport width in pixels"),
    sidebar_collapsed: bool = Query(default=False),
    is_authenticated: bool = Query(default=False),
) -> NavigationResolverResultContract:
    """Return full navigation resolver result: active item, parent, breadcrumbs, state, guards."""
    return resolve_navigation(
        route=route,
        viewport_width_px=viewport_width,
        sidebar_collapsed=sidebar_collapsed,
        is_authenticated=is_authenticated,
    )


@router.get(
    "/navigation/breadcrumbs",
    response_model=BreadcrumbChainContract,
    summary="Build breadcrumb chain for a route path",
)
def get_nav_breadcrumbs(
    route: str = Query(..., description="Route path (e.g. /shopping/products/123)"),
) -> BreadcrumbChainContract:
    """Return the typed breadcrumb chain with mobile_label and isTruncated metadata."""
    return build_breadcrumb_chain(route)


@router.get(
    "/navigation/guards",
    response_model=list[NavigationGuardResultContract],
    summary="Evaluate navigation item visibility for all routes",
)
def get_nav_guards(
    is_authenticated: bool = Query(default=False, description="Is the user authenticated?"),
    feature_flags: str = Query(default="", description="Comma-separated active feature flag keys"),
) -> list[NavigationGuardResultContract]:
    """Evaluate visibility (visible/hidden/disabled/restricted) for every navigation item."""
    active_flags: set[str] = {f.strip() for f in feature_flags.split(",") if f.strip()}
    registry = get_route_registry()
    return evaluate_navigation_guards(
        registry=registry,
        active_feature_flags=active_flags,
        is_authenticated=is_authenticated,
    )


@router.get(
    "/navigation/tabs/product",
    response_model=TabGroupContract,
    summary="Build product detail tab group for a product ID and active route",
)
def get_product_tab_group(
    product_id: str = Query(..., description="Product identifier (e.g. 'abc123')"),
    active_route: str = Query(default="", description="Current active route"),
) -> TabGroupContract:
    """Return the product detail tabs (Overview / Reviews / Specs / Styling) with active state."""
    return get_product_tabs(active_route=active_route, product_id=product_id)


@router.get(
    "/navigation/context",
    response_model=ContextNavigationContract,
    summary="Get context navigation for a named context",
)
def get_context_nav(
    context_id: str = Query(..., description="Context ID (e.g. 'profile-context-nav')"),
    active_route: str = Query(default="", description="Current active route"),
) -> ContextNavigationContract:
    """Return context navigation items with active state for a given page section."""
    ctx = get_context_navigation(context_id=context_id, active_route=active_route)
    if ctx is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Context navigation '{context_id}' not found",
        )
    return ctx


@router.get(
    "/navigation/error/404",
    response_model=NavigationErrorContract,
    summary="Build 404 navigation error contract",
)
def get_nav_404(
    route: str = Query(..., description="The attempted route that was not found"),
) -> NavigationErrorContract:
    """Return a typed 404 navigation error with recovery routes."""
    return build_404_error(route)


@router.get(
    "/navigation/error/data-failure",
    response_model=NavigationErrorContract,
    summary="Build data-failure navigation error contract",
)
def get_nav_data_failure(
    route: str = Query(..., description="The route that failed to load data"),
) -> NavigationErrorContract:
    """Return a typed data-failure error with Try Again + Return to Discover recovery."""
    return build_data_failure_error(route)
