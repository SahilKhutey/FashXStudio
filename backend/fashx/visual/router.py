"""FastAPI Router for FashXStudio Visual Layer Architecture & Design Tokens.

Exposes endpoints for Screen Inventory, Templates, Dependency Groups, Breakpoints, Domains,
and the Design Token System (Primitives, Semantic Themes, MST, Components, WCAG Validation).
Adheres to Rule I01 (Layer Separation) and Rule I19 (Standardized Error Envelopes).
"""

from typing import Any
from fastapi import APIRouter, HTTPException, Query, status

from fashx.core.errors import EntityNotFoundError
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


# ---------------------------------------------------------------------------
# Component Framework Endpoints (Phase 05)
# ---------------------------------------------------------------------------

from schemas.visual.components import (
    ComponentCatalogContract,
    ComponentDefinitionContract,
    ComponentValidationReportContract,
)
from .components_service import (
    get_component_catalog,
    get_component_definition,
    validate_component_props,
)


@router.get(
    "/components/catalog",
    response_model=ComponentCatalogContract,
    summary="Get complete catalog of Level 1 (Primitives) and Level 2 (Core UI) components",
)
def get_catalog() -> ComponentCatalogContract:
    """Return all primitive and core UI components with variants, sizing, and WCAG criteria."""
    return get_component_catalog()


@router.get(
    "/components/{name}",
    response_model=ComponentDefinitionContract,
    summary="Get component definition, tokens used, and accessibility criteria by name",
)
def get_component(name: str) -> ComponentDefinitionContract:
    """Find a specific component definition in the catalog."""
    component = get_component_definition(name)
    if not component:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Component '{name}' not found in component catalog",
        )
    return component


@router.post(
    "/components/validate",
    response_model=ComponentValidationReportContract,
    summary="Validate runtime props against component contract",
)
def validate_props(
    component_name: str = Query(..., description="Component name to validate against (e.g. Button, Input)"),
    props: dict[str, Any] = ...,
) -> ComponentValidationReportContract:
    """Validate component props payload against its strict Pydantic contract."""
    return validate_component_props(component_name=component_name, props=props)


# ---------------------------------------------------------------------------
# Fashion Content Endpoints (Phase 06)
# ---------------------------------------------------------------------------

from schemas.visual.fashion import (
    DiscoveryTemplateSpecContract,
    FashionContentType,
    FashionFeedContract,
    ListingTemplateSpecContract,
    SaveToggleRequestContract,
    SaveToggleResultContract,
    VisualContentModel,
)
from .fashion_service import (
    get_discovery_template,
    get_fashion_content,
    get_fashion_feed,
    get_listing_template,
    to_visual_content_model,
    toggle_content_save,
)


@router.get(
    "/fashion/feed",
    response_model=FashionFeedContract,
    summary="Get mixed fashion discovery feed",
)
def get_feed(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=50),
    content_type: FashionContentType | None = Query(default=None),
) -> FashionFeedContract:
    """Return a mixed discovery feed combining Stories, Looks, Products, Trends, and Collections."""
    return get_fashion_feed(page=page, limit=limit, content_type=content_type)


@router.get(
    "/fashion/content/{content_type}/{content_id}",
    summary="Get a specific fashion content item by type and ID",
)
def get_content_item(
    content_type: FashionContentType,
    content_id: str,
) -> dict[str, Any]:
    """Return raw or adapted fashion content object."""
    item = get_fashion_content(content_type, content_id)
    if not item:
        type_str = getattr(content_type, "value", str(content_type)).capitalize()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{type_str} '{content_id}' not found",
        )
    return item.model_dump()


@router.post(
    "/fashion/save-toggle",
    response_model=SaveToggleResultContract,
    summary="Toggle save/unsave for a fashion content item",
)
def post_save_toggle(
    payload: SaveToggleRequestContract,
) -> SaveToggleResultContract:
    """Execute save/unsave interaction with deterministic state machine."""
    return toggle_content_save(payload.content_type, payload.content_id, payload.current_saved)


@router.get(
    "/fashion/templates/discovery",
    response_model=DiscoveryTemplateSpecContract,
    summary="Get Discovery template specification payload",
)
def get_template_discovery() -> DiscoveryTemplateSpecContract:
    """Return template data for the top-level Discovery experience."""
    return get_discovery_template()


@router.get(
    "/fashion/templates/listing",
    response_model=ListingTemplateSpecContract,
    summary="Get Listing template specification payload",
)
def get_template_listing(
    category: str = Query(default="all"),
) -> ListingTemplateSpecContract:
    """Return template data for a catalog or look listing experience."""
    return get_listing_template(category=category)


# ---------------------------------------------------------------------------
# Shopping UI & Commerce Experience Endpoints (Phase 07)
# ---------------------------------------------------------------------------

from schemas.visual.shopping import (
    AddToCartRequestContract,
    CartContract,
    CartTemplateSpecContract,
    CartValidationResultContract,
    CategoryTemplateSpecContract,
    CheckoutStateContract,
    CheckoutSubmitRequestContract,
    CheckoutTemplateSpecContract,
    ConfirmationTemplateSpecContract,
    OrderDetailTemplateSpecContract,
    OrderContract,
    OrderReviewTemplateSpecContract,
    OrdersTemplateSpecContract,
    ProductComparisonContract,
    ProductDetailTemplateSpecContract,
    SearchResultsTemplateSpecContract,
    ShoppingHomeTemplateSpecContract,
    ShoppingProductDetailContract,
    SortOption,
    UpdateCartQuantityRequestContract,
    WishlistContract,
    WishlistTemplateSpecContract,
    WishlistToggleRequestContract,
    WishlistToggleResultContract,
)
from .shopping_service import (
    add_item_to_cart,
    compare_products,
    get_cart_template,
    get_category_template,
    get_checkout_template,
    get_confirmation_template,
    get_order_detail_template,
    get_order_review_template,
    get_orders_template,
    get_product_detail,
    get_product_detail_template,
    get_shopping_home_template,
    get_user_cart,
    get_wishlist_template,
    search_catalog_products,
    toggle_user_wishlist,
    update_cart_item_quantity,
    validate_cart_state,
)


@router.get(
    "/shopping/product/{product_id}",
    response_model=ShoppingProductDetailContract,
    summary="Get detailed shopping product data including variants and delivery",
)
def get_shopping_product(product_id: str) -> ShoppingProductDetailContract:
    """Retrieve product detail by ID."""
    prod = get_product_detail(product_id)
    if not prod:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Shopping product '{product_id}' not found",
        )
    return prod


@router.get(
    "/shopping/search",
    response_model=SearchResultsTemplateSpecContract,
    summary="Search catalog products with facet filters and sorting",
)
def search_products(
    q: str = Query(default=""),
    category: str | None = Query(default=None),
    sort: SortOption = Query(default=SortOption.RELEVANCE),
) -> SearchResultsTemplateSpecContract:
    """Search catalog items and retrieve filter facets."""
    return search_catalog_products(query=q, category=category, sort_option=sort)


@router.post(
    "/shopping/compare",
    response_model=ProductComparisonContract,
    summary="Compare attributes across multiple products",
)
def post_compare_products(product_ids: list[str]) -> ProductComparisonContract:
    """Generate product comparison matrix."""
    return compare_products(product_ids=product_ids)


@router.get(
    "/shopping/cart",
    response_model=CartContract,
    summary="Get user shopping cart",
)
def get_cart(cart_id: str = Query(default="cart-user-1")) -> CartContract:
    """Retrieve active user cart."""
    return get_user_cart(cart_id=cart_id)


@router.post(
    "/shopping/cart/add",
    response_model=CartContract,
    summary="Add product variant to shopping cart",
)
def post_add_to_cart(
    payload: AddToCartRequestContract,
    cart_id: str = Query(default="cart-user-1"),
) -> CartContract:
    """Add item to cart and recompute summary."""
    try:
        return add_item_to_cart(cart_id=cart_id, payload=payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/shopping/cart/update",
    response_model=CartContract,
    summary="Update quantity or remove item from shopping cart",
)
def post_update_cart_quantity(
    payload: UpdateCartQuantityRequestContract,
    cart_id: str = Query(default="cart-user-1"),
) -> CartContract:
    """Update line item quantity."""
    try:
        return update_cart_item_quantity(cart_id=cart_id, payload=payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/shopping/cart/validate",
    response_model=CartValidationResultContract,
    summary="Validate cart before proceeding to checkout",
)
def get_cart_validation(cart_id: str = Query(default="cart-user-1")) -> CartValidationResultContract:
    """Validate cart readiness."""
    return validate_cart_state(cart_id=cart_id)


@router.post(
    "/shopping/wishlist/toggle",
    response_model=WishlistToggleResultContract,
    summary="Toggle product presence in user wishlist",
)
def post_toggle_wishlist(
    payload: WishlistToggleRequestContract,
    user_id: str = Query(default="user-1"),
) -> WishlistToggleResultContract:
    """Execute wishlist toggle."""
    return toggle_user_wishlist(user_id=user_id, payload=payload)


# --- 12 Shopping Screen Templates (SH01 - SH12) ---

@router.get(
    "/shopping/templates/home",
    response_model=ShoppingHomeTemplateSpecContract,
    summary="SH01: Shopping Home template",
)
def get_template_shopping_home() -> ShoppingHomeTemplateSpecContract:
    return get_shopping_home_template()


@router.get(
    "/shopping/templates/category/{category_id}",
    response_model=CategoryTemplateSpecContract,
    summary="SH02: Category browsing template",
)
def get_template_category(category_id: str) -> CategoryTemplateSpecContract:
    return get_category_template(category_id=category_id)


@router.get(
    "/shopping/templates/product-detail/{product_id}",
    response_model=ProductDetailTemplateSpecContract,
    summary="SH07-adjacent: Product Detail template",
)
def get_template_product_detail(product_id: str) -> ProductDetailTemplateSpecContract:
    try:
        return get_product_detail_template(product_id=product_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/shopping/templates/wishlist",
    response_model=WishlistTemplateSpecContract,
    summary="SH05: Wishlist template",
)
def get_template_wishlist(user_id: str = Query(default="user-1")) -> WishlistTemplateSpecContract:
    return get_wishlist_template(user_id=user_id)


@router.get(
    "/shopping/templates/cart",
    response_model=CartTemplateSpecContract,
    summary="SH06: Shopping Cart template",
)
def get_template_cart(cart_id: str = Query(default="cart-user-1")) -> CartTemplateSpecContract:
    return get_cart_template(cart_id=cart_id)


@router.get(
    "/shopping/templates/checkout",
    response_model=CheckoutTemplateSpecContract,
    summary="SH08: Progressive Checkout template",
)
def get_template_checkout(checkout_id: str = Query(default="chk-101")) -> CheckoutTemplateSpecContract:
    return get_checkout_template(checkout_id=checkout_id)


@router.get(
    "/shopping/templates/order-review",
    response_model=OrderReviewTemplateSpecContract,
    summary="SH09: Order Review template",
)
def get_template_order_review(checkout_id: str = Query(default="chk-101")) -> OrderReviewTemplateSpecContract:
    return get_order_review_template(checkout_id=checkout_id)


@router.get(
    "/shopping/templates/confirmation",
    response_model=ConfirmationTemplateSpecContract,
    summary="SH10: Order Confirmation template",
)
def get_template_confirmation(order_id: str = Query(default="ord-98210")) -> ConfirmationTemplateSpecContract:
    return get_confirmation_template(order_id=order_id)


@router.get(
    "/shopping/templates/orders",
    response_model=OrdersTemplateSpecContract,
    summary="SH11: Customer Order History template",
)
def get_template_orders(user_id: str = Query(default="user-1")) -> OrdersTemplateSpecContract:
    return get_orders_template(user_id=user_id)


@router.get(
    "/shopping/templates/order-detail/{order_id}",
    response_model=OrderDetailTemplateSpecContract,
    summary="SH12: Order Detail template",
)
def get_template_order_detail(order_id: str) -> OrderDetailTemplateSpecContract:
    try:
        return get_order_detail_template(order_id=order_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ---------------------------------------------------------------------------
# Discovery + Search Screens Endpoints (Phase 08)
# ---------------------------------------------------------------------------

from schemas.visual.discovery import (
    AdvancedSearchCriteriaContract,
    AdvancedSearchTemplateSpecContract,
    DiscoveryHeroContract,
    DiscoveryHomeTemplateSpecContract,
    ExploreTemplateSpecContract,
    ExploreType,
    PersonalizedDiscoveryTemplateSpecContract,
    SearchResultsTemplateSpecContract as UnifiedSearchResultsTemplateSpecContract,
    SearchResultType,
    SearchHomeTemplateSpecContract,
    SearchSuggestionContract,
)
from .discovery_service import (
    execute_advanced_search,
    get_discovery_hero,
    get_discovery_home_template,
    get_explore_template,
    get_personalized_discovery_template,
    get_search_home_template,
    get_search_suggestions,
    search_unified_catalog,
)


@router.get(
    "/discovery/home",
    response_model=DiscoveryHomeTemplateSpecContract,
    summary="D01: Discovery Home gateway template",
)
def get_discovery_home() -> DiscoveryHomeTemplateSpecContract:
    """Return primary Discovery Home experience specification."""
    return get_discovery_home_template()


@router.get(
    "/discovery/hero",
    response_model=DiscoveryHeroContract,
    summary="Get Discovery Hero banner",
)
def get_hero() -> DiscoveryHeroContract:
    """Return configured hero banner."""
    return get_discovery_hero()


@router.get(
    "/discovery/explore/{explore_type}",
    response_model=ExploreTemplateSpecContract,
    summary="D02 - D08: Focused Explore template (fashion, products, looks, collections, brands, styles, trends)",
)
def get_explore_screen(explore_type: ExploreType) -> ExploreTemplateSpecContract:
    """Return explore screen template for specific content dimension."""
    return get_explore_template(explore_type=explore_type)


@router.get(
    "/discovery/personalized",
    response_model=PersonalizedDiscoveryTemplateSpecContract,
    summary="D09: Personalized Discovery template with explainability",
)
def get_personalized_discovery(user_id: str = Query(default="user-1")) -> PersonalizedDiscoveryTemplateSpecContract:
    """Return personalized discovery modules tailored to user profile."""
    return get_personalized_discovery_template(user_id=user_id)


@router.get(
    "/discovery/search-home",
    response_model=SearchHomeTemplateSpecContract,
    summary="S01: Search Home gateway with recent & trending queries",
)
def get_search_home() -> SearchHomeTemplateSpecContract:
    """Return search home gateway specification."""
    return get_search_home_template()


@router.get(
    "/discovery/suggestions",
    response_model=list[SearchSuggestionContract],
    summary="S02: Debounced search suggestions and autocomplete",
)
def get_suggestions(q: str = Query(default="")) -> list[SearchSuggestionContract]:
    """Retrieve autocomplete suggestions for query."""
    return get_search_suggestions(query=q)


@router.get(
    "/discovery/search",
    response_model=UnifiedSearchResultsTemplateSpecContract,
    summary="S03 - S07, S10: Multi-content search results across Products, Looks, Brands, Styles, Trends",
)
def get_search_results(
    q: str = Query(default=""),
    result_type: SearchResultType = Query(default=SearchResultType.ALL),
    sort: SortOption = Query(default=SortOption.RELEVANCE),
) -> UnifiedSearchResultsTemplateSpecContract:
    """Execute unified search across heterogeneous fashion dimensions."""
    return search_unified_catalog(query=q, result_type=result_type, sort=sort)


@router.post(
    "/discovery/advanced-search",
    response_model=AdvancedSearchTemplateSpecContract,
    summary="S09: Structured multi-attribute advanced search",
)
def post_advanced_search(criteria: AdvancedSearchCriteriaContract) -> AdvancedSearchTemplateSpecContract:
    """Execute structured advanced search query."""
    return execute_advanced_search(criteria=criteria)


# ---------------------------------------------------------------------------
# Product & Fashion Detail Screens Endpoints (Phase 09)
# ---------------------------------------------------------------------------

from schemas.visual.detail import (
    BrandStoryDetailTemplateSpecContract,
    ComprehensiveProductDetailTemplateSpecContract,
    EditorialViewTemplateSpecContract,
    FashionArticleDetailTemplateSpecContract,
    FashionCollectionDetailTemplateSpecContract,
    FashionInspirationDetailTemplateSpecContract,
    FashionLookDetailTemplateSpecContract,
    FashionStoryDetailTemplateSpecContract,
    ProductAvailabilityTemplateSpecContract,
    ProductComparisonTemplateSpecContract,
    ProductReviewsTemplateSpecContract,
)
from .detail_service import (
    get_brand_story_template,
    get_editorial_view_template,
    get_fashion_article_template,
    get_fashion_collection_template,
    get_fashion_inspiration_template,
    get_fashion_look_template,
    get_fashion_story_template,
    get_product_availability_template,
    get_product_comparison_template,
    get_product_detail_template as get_comprehensive_product_detail_template,
    get_product_reviews_template,
)


@router.get(
    "/detail/product/{product_id}",
    response_model=ComprehensiveProductDetailTemplateSpecContract,
    summary="P02: Product Detail screen specification with media, variants, specs & relationships",
)
def get_detail_product(product_id: str) -> ComprehensiveProductDetailTemplateSpecContract:
    """Retrieve comprehensive product detail view model."""
    return get_comprehensive_product_detail_template(product_id=product_id)


@router.get(
    "/detail/product/{product_id}/reviews",
    response_model=ProductReviewsTemplateSpecContract,
    summary="P05: Product Reviews screen specification with rating distribution and verified reviews",
)
def get_detail_product_reviews(product_id: str) -> ProductReviewsTemplateSpecContract:
    """Retrieve product reviews and star rating histogram."""
    return get_product_reviews_template(product_id=product_id)


@router.get(
    "/detail/product/{product_id}/availability",
    response_model=ProductAvailabilityTemplateSpecContract,
    summary="P10: Product Availability, stock units, and delivery estimates",
)
def get_detail_product_availability(product_id: str) -> ProductAvailabilityTemplateSpecContract:
    """Retrieve real-time inventory availability and fulfillment lead times."""
    return get_product_availability_template(product_id=product_id)


@router.post(
    "/detail/product/compare",
    response_model=ProductComparisonTemplateSpecContract,
    summary="P09: Product Comparison specification across multiple products",
)
def post_detail_product_compare(product_ids: list[str]) -> ProductComparisonTemplateSpecContract:
    """Generate side-by-side product comparison matrix."""
    return get_product_comparison_template(product_ids=product_ids)


@router.get(
    "/detail/fashion/story/{story_id}",
    response_model=FashionStoryDetailTemplateSpecContract,
    summary="F03: Fashion Story template specification",
)
def get_detail_fashion_story(story_id: str) -> FashionStoryDetailTemplateSpecContract:
    """Retrieve editorial fashion story detail."""
    return get_fashion_story_template(story_id=story_id)


@router.get(
    "/detail/fashion/article/{article_id}",
    response_model=FashionArticleDetailTemplateSpecContract,
    summary="F04: Fashion Article template specification",
)
def get_detail_fashion_article(article_id: str) -> FashionArticleDetailTemplateSpecContract:
    """Retrieve longform fashion article with inline media."""
    return get_fashion_article_template(article_id=article_id)


@router.get(
    "/detail/fashion/collection/{collection_id}",
    response_model=FashionCollectionDetailTemplateSpecContract,
    summary="F05: Fashion Collection template specification",
)
def get_detail_fashion_collection(collection_id: str) -> FashionCollectionDetailTemplateSpecContract:
    """Retrieve seasonal collection capsule detail."""
    return get_fashion_collection_template(collection_id=collection_id)


@router.get(
    "/detail/fashion/look/{look_id}",
    response_model=FashionLookDetailTemplateSpecContract,
    summary="F06: Fashion Look template specification with shoppable hotspots",
)
def get_detail_fashion_look(look_id: str) -> FashionLookDetailTemplateSpecContract:
    """Retrieve styled look detail with outfit constituent items and interactive hotspots."""
    return get_fashion_look_template(look_id=look_id)


@router.get(
    "/detail/fashion/inspiration/{inspiration_id}",
    response_model=FashionInspirationDetailTemplateSpecContract,
    summary="F07: Fashion Inspiration moodboard detail specification",
)
def get_detail_fashion_inspiration(inspiration_id: str) -> FashionInspirationDetailTemplateSpecContract:
    """Retrieve fashion inspiration moodboard with style tags and constituent links."""
    return get_fashion_inspiration_template(inspiration_id=inspiration_id)


@router.get(
    "/detail/fashion/brand/{brand_id}",
    response_model=BrandStoryDetailTemplateSpecContract,
    summary="F08: Brand Story detail specification with ethos and collections",
)
def get_detail_brand_story(brand_id: str) -> BrandStoryDetailTemplateSpecContract:
    """Retrieve brand heritage, values, collections, and verified merchant identity."""
    return get_brand_story_template(brand_id=brand_id)


@router.get(
    "/detail/fashion/editorial/{editorial_id}",
    response_model=EditorialViewTemplateSpecContract,
    summary="F09: Editorial View canvas with large visual rhythm",
)
def get_detail_editorial_view(editorial_id: str) -> EditorialViewTemplateSpecContract:
    """Retrieve high-rhythm editorial narrative with pull quotes and featured items."""
    return get_editorial_view_template(editorial_id=editorial_id)


# ---------------------------------------------------------------------------
# Outfit, Styling & Fashion Experience Endpoints (Phase 10)
# ---------------------------------------------------------------------------

from schemas.visual.styling import (
    AddSlotItemRequestContract,
    LookBuilderTemplateSpecContract,
    MixMatchTemplateSpecContract,
    OutfitBuilderTemplateSpecContract,
    OutfitContract,
    OutfitDetailTemplateSpecContract,
    OutfitPreviewTemplateSpecContract,
    ReplaceSlotItemRequestContract,
    SavedLookContract,
    SavedLooksTemplateSpecContract,
    SaveOutfitRequestContract,
    ShopOutfitAvailabilityContract,
    StyleHomeTemplateSpecContract,
    StylePreferenceContract,
    StylePreferencesTemplateSpecContract,
    StyleRecommendationTemplateSpecContract,
)
from .styling_service import (
    add_item_to_outfit,
    delete_saved_look,
    duplicate_saved_look,
    get_look_builder_template,
    get_mix_match_template,
    get_outfit_builder_template,
    get_outfit_detail_template,
    get_outfit_preview_template,
    get_saved_looks_template,
    get_style_home_template,
    get_style_preferences_template,
    get_style_recommendation_template,
    remove_item_from_outfit,
    replace_item_in_outfit,
    reset_outfit_slots,
    save_outfit_as_look,
    update_style_preferences,
    validate_outfit_for_shopping,
)


@router.get(
    "/styling/home",
    response_model=StyleHomeTemplateSpecContract,
    summary="ST01: Style Home gateway specification",
)
def get_styling_home() -> StyleHomeTemplateSpecContract:
    """Retrieve primary Style Home screen specification."""
    return get_style_home_template()


@router.get(
    "/styling/builder",
    response_model=OutfitBuilderTemplateSpecContract,
    summary="ST02: Primary interactive outfit workspace",
)
def get_styling_builder(outfit_id: str | None = Query(default=None)) -> OutfitBuilderTemplateSpecContract:
    """Retrieve outfit builder workspace state."""
    return get_outfit_builder_template(outfit_id=outfit_id)


@router.post(
    "/styling/builder/{outfit_id}/add",
    response_model=OutfitContract,
    summary="Add product into an outfit slot",
)
def post_outfit_add_item(outfit_id: str, payload: AddSlotItemRequestContract) -> OutfitContract:
    """Assign product item to designated slot."""
    return add_item_to_outfit(outfit_id=outfit_id, payload=payload)


@router.post(
    "/styling/builder/{outfit_id}/replace",
    response_model=OutfitContract,
    summary="Replace existing product in an outfit slot",
)
def post_outfit_replace_item(outfit_id: str, payload: ReplaceSlotItemRequestContract) -> OutfitContract:
    """Swap existing slot item with alternative product choice."""
    return replace_item_in_outfit(outfit_id=outfit_id, payload=payload)


@router.delete(
    "/styling/builder/{outfit_id}/slot/{slot_id}",
    response_model=OutfitContract,
    summary="Remove item from designated outfit slot",
)
def delete_outfit_item(outfit_id: str, slot_id: str) -> OutfitContract:
    """Reset slot to empty."""
    return remove_item_from_outfit(outfit_id=outfit_id, slot_id=slot_id)


@router.post(
    "/styling/builder/{outfit_id}/reset",
    response_model=OutfitContract,
    summary="Reset all slots in the outfit to empty",
)
def post_outfit_reset(outfit_id: str) -> OutfitContract:
    """Clear all occupied slots."""
    return reset_outfit_slots(outfit_id=outfit_id)


@router.get(
    "/styling/look-builder",
    response_model=LookBuilderTemplateSpecContract,
    summary="ST03: Creative visual look builder canvas",
)
def get_styling_look_builder(look_id: str | None = Query(default=None)) -> LookBuilderTemplateSpecContract:
    """Retrieve creative look builder canvas."""
    return get_look_builder_template(look_id=look_id)


@router.get(
    "/styling/mix-match",
    response_model=MixMatchTemplateSpecContract,
    summary="ST04: Mix & Match rapid experimentation matrix",
)
def get_styling_mix_match(outfit_id: str | None = Query(default=None)) -> MixMatchTemplateSpecContract:
    """Retrieve Mix & Match candidate matrix for active outfit."""
    return get_mix_match_template(outfit_id=outfit_id)


@router.get(
    "/styling/recommendation",
    response_model=StyleRecommendationTemplateSpecContract,
    summary="ST05: Explainable style recommendations",
)
def get_styling_recommendation(user_id: str = Query(default="user-1")) -> StyleRecommendationTemplateSpecContract:
    """Retrieve personalized style recommendation with explainability rationale."""
    return get_style_recommendation_template(user_id=user_id)


@router.get(
    "/styling/preview/{outfit_id}",
    response_model=OutfitPreviewTemplateSpecContract,
    summary="ST06: Clean read-only outfit composition preview",
)
def get_styling_preview(outfit_id: str) -> OutfitPreviewTemplateSpecContract:
    """Retrieve non-editable outfit preview."""
    return get_outfit_preview_template(outfit_id=outfit_id)


@router.get(
    "/styling/detail/{outfit_id}",
    response_model=OutfitDetailTemplateSpecContract,
    summary="ST07: Comprehensive outfit detail with shoppable pieces",
)
def get_styling_detail(outfit_id: str) -> OutfitDetailTemplateSpecContract:
    """Retrieve complete outfit detail with constituent product links."""
    return get_outfit_detail_template(outfit_id=outfit_id)


@router.get(
    "/styling/validate-shop/{outfit_id}",
    response_model=ShopOutfitAvailabilityContract,
    summary="Validate outfit availability before cart handoff",
)
def get_styling_validate_shop(outfit_id: str) -> ShopOutfitAvailabilityContract:
    """Evaluate inventory and pricing integrity before cart transfer."""
    return validate_outfit_for_shopping(outfit_id=outfit_id)


@router.get(
    "/styling/saved-looks",
    response_model=SavedLooksTemplateSpecContract,
    summary="ST08: User saved looks archive and collection manager",
)
def get_styling_saved_looks(
    user_id: str = Query(default="user-1"),
    filter_tag: str = Query(default="all"),
) -> SavedLooksTemplateSpecContract:
    """Retrieve saved looks collection."""
    return get_saved_looks_template(user_id=user_id, filter_tag=filter_tag)


@router.post(
    "/styling/saved-looks",
    response_model=SavedLookContract,
    summary="Save an outfit as a persistent saved look",
)
def post_styling_save_look(payload: SaveOutfitRequestContract) -> SavedLookContract:
    """Persist outfit into saved looks archive."""
    return save_outfit_as_look(payload=payload)


@router.post(
    "/styling/saved-looks/{look_id}/duplicate",
    response_model=SavedLookContract,
    summary="Duplicate a saved look for experimentation",
)
def post_styling_duplicate_look(look_id: str) -> SavedLookContract:
    """Clone saved look into a new editable instance."""
    return duplicate_saved_look(look_id=look_id)


@router.delete(
    "/styling/saved-looks/{look_id}",
    response_model=dict[str, bool],
    summary="Delete a saved look from the user archive",
)
def delete_styling_saved_look(look_id: str) -> dict[str, bool]:
    """Remove saved look from registry."""
    success = delete_saved_look(look_id=look_id)
    return {"success": success}


@router.get(
    "/styling/preferences",
    response_model=StylePreferencesTemplateSpecContract,
    summary="ST09: User style preference settings",
)
def get_styling_preferences(user_id: str = Query(default="user-1")) -> StylePreferencesTemplateSpecContract:
    """Retrieve user aesthetic preference profile."""
    return get_style_preferences_template(user_id=user_id)


@router.put(
    "/styling/preferences",
    response_model=StylePreferenceContract,
    summary="Update user style preferences",
)
def put_styling_preferences(
    preferences: StylePreferenceContract,
    user_id: str = Query(default="user-1"),
) -> StylePreferenceContract:
    """Persist updated style preferences."""
    return update_style_preferences(user_id=user_id, preferences=preferences)


# ---------------------------------------------------------------------------
# Regional Maps & Geography Endpoints (Phase 11)
# ---------------------------------------------------------------------------

from schemas.visual.geography import (
    CityTemplateSpecContract,
    CountryTemplateSpecContract,
    FashionMapTemplateSpecContract,
    GeographyLayerType,
    LocalProductsTemplateSpecContract,
    LocationDetailTemplateSpecContract,
    RegionBreadcrumbContract,
    RegionContract,
    RegionType,
    RegionalCollectionsTemplateSpecContract,
    RegionalComparisonContract,
    RegionalExplorerTemplateSpecContract,
    RegionalHomeTemplateSpecContract,
    RegionalTrendContract,
    RegionalTrendsTemplateSpecContract,
    StateTemplateSpecContract,
)
from .geography_service import (
    compare_regions,
    get_city_template,
    get_country_template,
    get_fashion_map_template,
    get_local_products_template,
    get_location_detail_template,
    get_region_breadcrumbs,
    get_regional_collections_template,
    get_regional_explorer_template,
    get_regional_home_template,
    get_regional_trends_template,
    get_state_template,
    search_regions,
)


@router.get(
    "/geography/home",
    response_model=RegionalHomeTemplateSpecContract,
    summary="M01: Regional Home gateway specification",
)
def get_geo_home() -> RegionalHomeTemplateSpecContract:
    """Retrieve Regional Home gateway specification."""
    return get_regional_home_template()


@router.get(
    "/geography/map",
    response_model=FashionMapTemplateSpecContract,
    summary="M02: Primary interactive fashion map specification",
)
def get_geo_map(region_id: str | None = Query(default=None)) -> FashionMapTemplateSpecContract:
    """Retrieve fashion map viewport, markers, and selected region."""
    return get_fashion_map_template(region_id=region_id)


@router.get(
    "/geography/explorer",
    response_model=RegionalExplorerTemplateSpecContract,
    summary="M03: Hierarchical accessible text/list browsing explorer",
)
def get_geo_explorer(
    parent_id: str | None = Query(default=None),
    q: str = Query(default=""),
) -> RegionalExplorerTemplateSpecContract:
    """Retrieve hierarchical region explorer view."""
    return get_regional_explorer_template(parent_id=parent_id, query=q)


@router.get(
    "/geography/country/{country_id}",
    response_model=CountryTemplateSpecContract,
    summary="M04: Country level fashion culture canvas",
)
def get_geo_country(country_id: str) -> CountryTemplateSpecContract:
    """Retrieve country-level fashion culture view."""
    return get_country_template(country_id=country_id)


@router.get(
    "/geography/state/{state_id}",
    response_model=StateTemplateSpecContract,
    summary="M05: State or province level fashion canvas",
)
def get_geo_state(state_id: str) -> StateTemplateSpecContract:
    """Retrieve state-level fashion view."""
    return get_state_template(state_id=state_id)


@router.get(
    "/geography/city/{city_id}",
    response_model=CityTemplateSpecContract,
    summary="M06: City and urban fashion hub canvas",
)
def get_geo_city(city_id: str) -> CityTemplateSpecContract:
    """Retrieve city-level fashion hub view."""
    return get_city_template(city_id=city_id)


@router.get(
    "/geography/trends/{region_id}",
    response_model=RegionalTrendsTemplateSpecContract,
    summary="M07: Dedicated regional trends feed",
)
def get_geo_trends(region_id: str) -> RegionalTrendsTemplateSpecContract:
    """Retrieve localized fashion trends for region."""
    return get_regional_trends_template(region_id=region_id)


@router.get(
    "/geography/products/{region_id}",
    response_model=LocalProductsTemplateSpecContract,
    summary="M08: Localized products listing reusing commerce grid",
)
def get_geo_products(region_id: str) -> LocalProductsTemplateSpecContract:
    """Retrieve local products for region."""
    return get_local_products_template(region_id=region_id)


@router.get(
    "/geography/collections/{region_id}",
    response_model=RegionalCollectionsTemplateSpecContract,
    summary="M09: Regional capsule collections specification",
)
def get_geo_collections(region_id: str) -> RegionalCollectionsTemplateSpecContract:
    """Retrieve curated regional capsule collections."""
    return get_regional_collections_template(region_id=region_id)


@router.get(
    "/geography/location/{location_id}",
    response_model=LocationDetailTemplateSpecContract,
    summary="M10: Deep contextual location profile",
)
def get_geo_location(location_id: str) -> LocationDetailTemplateSpecContract:
    """Retrieve comprehensive contextual location view."""
    return get_location_detail_template(location_id=location_id)


@router.get(
    "/geography/search",
    response_model=list[RegionContract],
    summary="Search regions with entity classification type filtering",
)
def get_geo_search(
    q: str = Query(default=""),
    region_type: RegionType | None = Query(default=None),
) -> list[RegionContract]:
    """Search region entities by query and optional type."""
    return search_regions(query=q, region_type=region_type)


@router.post(
    "/geography/compare",
    response_model=RegionalComparisonContract,
    summary="Factual side-by-side geographic fashion comparison matrix",
)
def post_geo_compare(region_ids: list[str]) -> RegionalComparisonContract:
    """Generate regional comparison matrix."""
    return compare_regions(region_ids=region_ids)


@router.get(
    "/geography/breadcrumbs/{region_id}",
    response_model=list[RegionBreadcrumbContract],
    summary="Hierarchical geographic breadcrumbs from root to leaf",
)
def get_geo_breadcrumbs(region_id: str) -> list[RegionBreadcrumbContract]:
    """Retrieve ordered breadcrumbs for region."""
    return get_region_breadcrumbs(region_id=region_id)


# ---------------------------------------------------------------------------
# AI / Intelligence Endpoints (Phase 12)
# ---------------------------------------------------------------------------

from schemas.visual.ai import (
    AIAssistantTemplateSpecContract,
    AIFeedbackContract,
    AIHomeTemplateSpecContract,
    AIMessageContract,
    AIOutfitRecommendationTemplateSpecContract,
    AIPreferencesContract,
    AIPreferencesTemplateSpecContract,
    AIProductAssistantTemplateSpecContract,
    AIRecommendationDetailTemplateSpecContract,
    AIResultExplanationTemplateSpecContract,
    AISearchTemplateSpecContract,
    AISessionContract,
    AIStyleAssistantTemplateSpecContract,
    PostAIFeedbackRequestContract,
    PostAIMessageRequestContract,
)
from .ai_service import (
    ai_search,
    create_ai_session,
    get_ai_assistant_template,
    get_ai_home_template,
    get_ai_preferences,
    get_ai_session,
    get_outfit_recommendation_template,
    get_product_assistant_template,
    get_recommendation_detail,
    get_result_explanation,
    get_style_assistant_template,
    post_ai_message,
    submit_ai_feedback,
    update_ai_preferences,
)


@router.get(
    "/ai/home",
    response_model=AIHomeTemplateSpecContract,
    summary="AI01: AI Home central intelligence entry point",
)
def get_ai_home() -> AIHomeTemplateSpecContract:
    """Retrieve AI Home gateway specification."""
    return get_ai_home_template()


@router.post(
    "/ai/session",
    response_model=AISessionContract,
    summary="Instantiate a new conversation session",
)
def post_create_session(title: str = Query(default="New Fashion Session")) -> AISessionContract:
    """Create a new AI conversation session."""
    return create_ai_session(title=title)


@router.get(
    "/ai/session/{session_id}",
    response_model=AISessionContract,
    summary="Retrieve an active or archived conversation session",
)
def get_session(session_id: str) -> AISessionContract:
    """Retrieve AI session details and message history."""
    return get_ai_session(session_id=session_id)


@router.post(
    "/ai/session/{session_id}/message",
    response_model=AIMessageContract,
    summary="Post user message and generate transparent assistant reply",
)
def post_session_message(
    session_id: str,
    payload: PostAIMessageRequestContract,
) -> AIMessageContract:
    """Append user message and return assistant reply."""
    return post_ai_message(
        session_id=session_id,
        content=payload.content,
        context_items=payload.context_items,
    )


@router.get(
    "/ai/assistant",
    response_model=AIAssistantTemplateSpecContract,
    summary="AI02: Multi-turn conversational fashion assistant",
)
def get_assistant(session_id: str | None = Query(default=None)) -> AIAssistantTemplateSpecContract:
    """Retrieve conversational assistant template."""
    return get_ai_assistant_template(session_id=session_id)


@router.get(
    "/ai/product-assistant/{product_id}",
    response_model=AIProductAssistantTemplateSpecContract,
    summary="AI03: Product-specific Q&A with strict fact vs guidance separation",
)
def get_product_assistant(product_id: str) -> AIProductAssistantTemplateSpecContract:
    """Retrieve product assistant view with catalog facts separated from AI styling guidance."""
    return get_product_assistant_template(product_id=product_id)


@router.get(
    "/ai/style-assistant",
    response_model=AIStyleAssistantTemplateSpecContract,
    summary="AI04: Aesthetic recommendation with explainable matching",
)
def get_style_assistant(style_id: str | None = Query(default=None)) -> AIStyleAssistantTemplateSpecContract:
    """Retrieve style assistant recommendation view."""
    return get_style_assistant_template(style_id=style_id)


@router.get(
    "/ai/outfit-recommendation",
    response_model=AIOutfitRecommendationTemplateSpecContract,
    summary="AI05: AI outfit recommendation with user editing controls",
)
def get_outfit_recommendation(look_id: str | None = Query(default=None)) -> AIOutfitRecommendationTemplateSpecContract:
    """Retrieve outfit recommendation template with wearability explanations."""
    return get_outfit_recommendation_template(look_id=look_id)


@router.get(
    "/ai/search",
    response_model=AISearchTemplateSpecContract,
    summary="AI06: Natural language query search with intent understanding",
)
def get_ai_search(q: str = Query(default="")) -> AISearchTemplateSpecContract:
    """Execute natural language search with multi-stage observable steps."""
    return ai_search(query=q)


@router.get(
    "/ai/recommendation/{recommendation_id}",
    response_model=AIRecommendationDetailTemplateSpecContract,
    summary="AI07: Deep dive into an individual recommendation",
)
def get_recommendation_detail_endpoint(recommendation_id: str) -> AIRecommendationDetailTemplateSpecContract:
    """Retrieve recommendation detail specification."""
    return get_recommendation_detail(recommendation_id=recommendation_id)


@router.get(
    "/ai/explanation/{result_id}",
    response_model=AIResultExplanationTemplateSpecContract,
    summary="AI08: Dedicated why this result explanation canvas",
)
def get_explanation_endpoint(result_id: str) -> AIResultExplanationTemplateSpecContract:
    """Retrieve detailed explanation for a result."""
    return get_result_explanation(result_id=result_id)


@router.get(
    "/ai/preferences",
    response_model=AIPreferencesTemplateSpecContract,
    summary="AI09: AI tuning preferences control canvas",
)
def get_preferences(user_id: str = Query(default="user-default")) -> AIPreferencesTemplateSpecContract:
    """Retrieve user AI preferences."""
    return get_ai_preferences(user_id=user_id)


@router.put(
    "/ai/preferences",
    response_model=AIPreferencesContract,
    summary="Update user AI tuning preferences",
)
def put_preferences(payload: AIPreferencesContract) -> AIPreferencesContract:
    """Update AI preferences."""
    return update_ai_preferences(preferences=payload)


@router.post(
    "/ai/feedback",
    response_model=AIFeedbackContract,
    summary="Explicit user evaluation of AI output",
)
def post_feedback(payload: PostAIFeedbackRequestContract) -> AIFeedbackContract:
    """Submit evaluation feedback for an AI result."""
    return submit_ai_feedback(
        result_id=payload.result_id,
        feedback_type=payload.feedback_type,
        reason=payload.reason,
        note=payload.note,
    )


# ---------------------------------------------------------------------------
# Profile, Personalization & Saved Space Endpoints (Phase 13)
# ---------------------------------------------------------------------------

from schemas.visual.personal import (
    AccountSettingsTemplateSpecContract,
    ClearHistoryRequestContract,
    PersonalDashboardTemplateSpecContract,
    PreferencesTemplateSpecContract,
    ProfileTemplateSpecContract,
    RecentlyViewedTemplateSpecContract,
    RecommendationPreferencesTemplateSpecContract,
    RegionalPreferencesTemplateSpecContract,
    SavedFashionTemplateSpecContract,
    SavedItemToggleRequestContract,
    SavedItemToggleResultContract,
    SavedItemType,
    SavedLooksTemplateSpecContract,
    SavedProductsTemplateSpecContract,
    UpdateAccountSettingsRequestContract,
    UpdateExplicitPreferencesRequestContract,
    UpdateRecommendationPreferencesRequestContract,
    UpdateRegionalPreferencesRequestContract,
    WishlistTemplateSpecContract,
)
from .personal_service import (
    clear_recently_viewed_history,
    get_account_settings_template,
    get_personal_dashboard_template,
    get_personal_saved_looks_template,
    get_personal_wishlist_template,
    get_preferences_template,
    get_profile_template,
    get_recently_viewed_template,
    get_recommendation_preferences_template,
    get_regional_preferences_template,
    get_saved_fashion_template,
    get_saved_products_template,
    remove_saved_item,
    reset_personalization_signals,
    toggle_saved_item,
    update_account_settings,
    update_explicit_preferences,
    update_recommendation_preferences,
    update_regional_preferences,
)


@router.get(
    "/personal/profile",
    response_model=ProfileTemplateSpecContract,
    summary="PR01: User Profile main personal space",
)
def get_profile_endpoint(user_id: str = Query(default="usr_fashx_01")) -> ProfileTemplateSpecContract:
    """Retrieve personal profile specification."""
    return get_profile_template(user_id=user_id)


@router.get(
    "/personal/dashboard",
    response_model=PersonalDashboardTemplateSpecContract,
    summary="PR02: Personal Dashboard prioritizing Continue -> Saved -> Recommendations",
)
def get_personal_dashboard_endpoint(
    user_id: str = Query(default="usr_fashx_01"),
    fail_recommendations: bool = Query(default=False),
) -> PersonalDashboardTemplateSpecContract:
    """Retrieve personal dashboard specification with graceful module degradation."""
    return get_personal_dashboard_template(
        user_id=user_id,
        fail_recommendations=fail_recommendations,
    )


@router.get(
    "/personal/saved/products",
    response_model=SavedProductsTemplateSpecContract,
    summary="PR03: Saved products catalog with filter and sort",
)
def get_saved_products_endpoint(
    filter_category: str | None = Query(default=None),
    sort_by: str = Query(default="recently_saved"),
) -> SavedProductsTemplateSpecContract:
    """Retrieve saved products list."""
    return get_saved_products_template(filter_category=filter_category, sort_by=sort_by)


@router.get(
    "/personal/saved/looks",
    response_model=SavedLooksTemplateSpecContract,
    summary="PR04: Saved outfit collections and looks canvas",
)
def get_saved_looks_endpoint(
    collection_id: str | None = Query(default=None),
) -> SavedLooksTemplateSpecContract:
    """Retrieve saved looks grouped by collection."""
    return get_personal_saved_looks_template(collection_id=collection_id)


@router.get(
    "/personal/saved/fashion",
    response_model=SavedFashionTemplateSpecContract,
    summary="PR05: Saved editorial stories, trends, and inspiration",
)
def get_saved_fashion_endpoint(
    tab: str = Query(default="all"),
) -> SavedFashionTemplateSpecContract:
    """Retrieve saved fashion content filtered by tab."""
    return get_saved_fashion_template(tab=tab)


@router.get(
    "/personal/wishlist",
    response_model=WishlistTemplateSpecContract,
    summary="PR06: Commercial wishlist with availability tracking",
)
def get_wishlist_endpoint() -> WishlistTemplateSpecContract:
    """Retrieve wishlist specification."""
    return get_personal_wishlist_template()


@router.get(
    "/personal/recent",
    response_model=RecentlyViewedTemplateSpecContract,
    summary="PR07: Browsing activity history",
)
def get_recently_viewed_endpoint(
    entity_type: str | None = Query(default=None),
) -> RecentlyViewedTemplateSpecContract:
    """Retrieve recently viewed history."""
    return get_recently_viewed_template(entity_type=entity_type)


@router.post(
    "/personal/recent/clear",
    summary="PR07: Clear browsing activity history",
)
def post_clear_recent_history(
    payload: ClearHistoryRequestContract | None = None,
) -> dict[str, Any]:
    """Clear browsing activity history."""
    et = payload.entity_type.value if payload and payload.entity_type else None
    return clear_recently_viewed_history(entity_type=et)


@router.get(
    "/personal/preferences",
    response_model=PreferencesTemplateSpecContract,
    summary="PR08: Modular explicit style and wardrobe preferences",
)
def get_preferences_endpoint() -> PreferencesTemplateSpecContract:
    """Retrieve user explicit and inferred preferences."""
    return get_preferences_template()


@router.put(
    "/personal/preferences",
    response_model=PreferencesTemplateSpecContract,
    summary="PR08: Update explicit preferences",
)
def put_preferences_endpoint(
    payload: UpdateExplicitPreferencesRequestContract,
) -> PreferencesTemplateSpecContract:
    """Update explicit preferences."""
    return update_explicit_preferences(payload=payload)


@router.get(
    "/personal/preferences/recommendations",
    response_model=RecommendationPreferencesTemplateSpecContract,
    summary="PR09: Algorithmic recommendation tuning & transparency",
)
def get_recommendation_preferences_endpoint() -> RecommendationPreferencesTemplateSpecContract:
    """Retrieve recommendation preferences specification."""
    return get_recommendation_preferences_template()


@router.put(
    "/personal/preferences/recommendations",
    response_model=RecommendationPreferencesTemplateSpecContract,
    summary="PR09: Update recommendation toggle controls",
)
def put_recommendation_preferences_endpoint(
    payload: UpdateRecommendationPreferencesRequestContract,
) -> RecommendationPreferencesTemplateSpecContract:
    """Update recommendation preferences."""
    return update_recommendation_preferences(payload=payload)


@router.post(
    "/personal/preferences/recommendations/reset",
    response_model=RecommendationPreferencesTemplateSpecContract,
    summary="PR09: Reset personalization signals and inferred history",
)
def post_reset_personalization_endpoint() -> RecommendationPreferencesTemplateSpecContract:
    """Reset personalization signals."""
    return reset_personalization_signals()


@router.get(
    "/personal/preferences/regional",
    response_model=RegionalPreferencesTemplateSpecContract,
    summary="PR10: Regional fashion culture context preferences",
)
def get_regional_preferences_endpoint() -> RegionalPreferencesTemplateSpecContract:
    """Retrieve regional preferences specification."""
    return get_regional_preferences_template()


@router.put(
    "/personal/preferences/regional",
    response_model=RegionalPreferencesTemplateSpecContract,
    summary="PR10: Update regional preferences",
)
def put_regional_preferences_endpoint(
    payload: UpdateRegionalPreferencesRequestContract,
) -> RegionalPreferencesTemplateSpecContract:
    """Update regional preferences."""
    return update_regional_preferences(payload=payload)


@router.get(
    "/personal/settings",
    response_model=AccountSettingsTemplateSpecContract,
    summary="PR11: Account security, notification & privacy settings",
)
def get_account_settings_endpoint() -> AccountSettingsTemplateSpecContract:
    """Retrieve account settings specification."""
    return get_account_settings_template()


@router.put(
    "/personal/settings",
    response_model=AccountSettingsTemplateSpecContract,
    summary="PR11: Update account settings",
)
def put_account_settings_endpoint(
    payload: UpdateAccountSettingsRequestContract,
) -> AccountSettingsTemplateSpecContract:
    """Update account settings."""
    return update_account_settings(payload=payload)


@router.post(
    "/personal/saved/toggle",
    response_model=SavedItemToggleResultContract,
    summary="Toggle save state for product, look, fashion, or wishlist",
)
def post_toggle_saved_item_endpoint(
    payload: SavedItemToggleRequestContract,
) -> SavedItemToggleResultContract:
    """Toggle save state for an item."""
    return toggle_saved_item(payload=payload)


@router.delete(
    "/personal/saved/{item_type}/{item_id}",
    response_model=SavedItemToggleResultContract,
    summary="Explicitly remove saved item",
)
def delete_saved_item_endpoint(
    item_type: SavedItemType,
    item_id: str,
) -> SavedItemToggleResultContract:
    """Remove item from saved registry."""
    return remove_saved_item(item_type=item_type, item_id=item_id)


# ---------------------------------------------------------------------------
# Responsive & Adaptive Visual System Endpoints (Phase 14)
# ---------------------------------------------------------------------------

from schemas.visual.responsive import (
    CardContentPruningRequest,
    CardContentPruningResult,
    CrossSystemScreenResponsiveContract,
    ResponsiveBreakpoint,
    ResponsiveContainerContract,
    ResponsiveGridCalculationRequest,
    ResponsiveGridCalculationResult,
    ViewportEvaluationRequest,
    ViewportEvaluationResult,
)
from .responsive_service import (
    CONTAINER_CONFIGS,
    calculate_fluid_grid,
    evaluate_viewport,
    get_cross_system_screen_qa,
    prune_card_content,
    resolve_breakpoint,
    resolve_container_config,
)


@router.get(
    "/responsive/breakpoints",
    response_model=list[ResponsiveBreakpoint],
    summary="List all responsive layout thresholds (XS, SM, MD, LG, XL, 2XL)",
)
def get_responsive_breakpoints() -> list[ResponsiveBreakpoint]:
    """Retrieve all supported responsive breakpoint layout thresholds."""
    return list(CONTAINER_CONFIGS.keys())


@router.get(
    "/responsive/containers",
    response_model=list[ResponsiveContainerContract],
    summary="List master container specifications and boundaries",
)
def get_responsive_containers() -> list[ResponsiveContainerContract]:
    """Retrieve master container constraints, gutters, and paddings for all breakpoints."""
    return list(CONTAINER_CONFIGS.values())


@router.post(
    "/responsive/evaluate",
    response_model=ViewportEvaluationResult,
    summary="Evaluate viewport dimensions and return responsive layout directives",
)
def post_evaluate_viewport(payload: ViewportEvaluationRequest) -> ViewportEvaluationResult:
    """Evaluate viewport width, height, and input mode into deterministic layout directives."""
    return evaluate_viewport(request=payload)


@router.post(
    "/responsive/grid-calculate",
    response_model=ResponsiveGridCalculationResult,
    summary="Compute optimal fluid columns and card width without breakpoint-heavy code",
)
def post_calculate_fluid_grid(
    payload: ResponsiveGridCalculationRequest,
) -> ResponsiveGridCalculationResult:
    """Calculate fluid grid columns, exact item width, and container utilization."""
    return calculate_fluid_grid(request=payload)


@router.post(
    "/responsive/card-prune",
    response_model=CardContentPruningResult,
    summary="Prune card metadata according to content priority (P0-P3) and layout mode",
)
def post_prune_card_content(payload: CardContentPruningRequest) -> CardContentPruningResult:
    """Evaluate content priority pruning for a card based on available space."""
    return prune_card_content(request=payload)


@router.get(
    "/responsive/screen-qa/{screen_id}",
    response_model=CrossSystemScreenResponsiveContract,
    summary="Verify cross-system screen responsiveness across earlier phases (VD-03 to VD-13)",
)
def get_screen_responsive_qa(
    screen_id: str,
    width_px: int = Query(default=390, gt=0),
) -> CrossSystemScreenResponsiveContract:
    """Validate screen responsive layout mode, density, and sticky actions."""
    return get_cross_system_screen_qa(screen_id=screen_id, width_px=width_px)


# ---------------------------------------------------------------------------
# Interaction, State, Accessibility & Visual QA System Endpoints (Phase 15)
# ---------------------------------------------------------------------------

from schemas.visual.interaction import (
    AccessibilityAuditRequest,
    AccessibilityAuditResult,
    ComponentStateContract,
    ComponentStateEvaluationRequest,
    FeedbackDispatchRequest,
    FeedbackEventContract,
    FormFieldValidationRequest,
    FormFieldValidationResult,
    ScreenLifecycleState,
    ScreenStateContract,
    VisualQASpecContract,
)
from .interaction_service import (
    dispatch_feedback_event,
    evaluate_component_state,
    get_screen_state,
    list_visual_qa_fixtures,
    run_accessibility_audit,
    validate_form_field,
)


@router.post(
    "/interaction/component-state",
    response_model=ComponentStateContract,
    summary="Evaluate active component state under strict precedence hierarchy",
)
def post_evaluate_component_state(
    payload: ComponentStateEvaluationRequest,
) -> ComponentStateContract:
    """Resolve component interaction state (Error > Disabled > Loading > Selected > etc.)."""
    return evaluate_component_state(request=payload)


@router.post(
    "/interaction/form-validate",
    response_model=FormFieldValidationResult,
    summary="Validate form field input with contextual fix guidance",
)
def post_validate_form_field(
    payload: FormFieldValidationRequest,
) -> FormFieldValidationResult:
    """Validate form field and return actionable guidance and ARIA invalid attributes."""
    return validate_form_field(request=payload)


@router.post(
    "/interaction/feedback/dispatch",
    response_model=FeedbackEventContract,
    summary="Determine optimal, accessible feedback mechanism (Toast, Alert, Banner, Dialog)",
)
def post_dispatch_feedback(payload: FeedbackDispatchRequest) -> FeedbackEventContract:
    """Map situation to the least-disruptive, accessible feedback presentation."""
    return dispatch_feedback_event(request=payload)


@router.get(
    "/interaction/screen-state/{screen_id}",
    response_model=ScreenStateContract,
    summary="Retrieve screen lifecycle state (loading, empty, error, partial, offline)",
)
def get_screen_lifecycle_state(
    screen_id: str,
    lifecycle_state: ScreenLifecycleState = Query(default=ScreenLifecycleState.LOADED),
) -> ScreenStateContract:
    """Retrieve screen lifecycle specifications, skeletons, and error recovery guidance."""
    return get_screen_state(screen_id=screen_id, lifecycle_state=lifecycle_state)


@router.post(
    "/interaction/accessibility-audit",
    response_model=AccessibilityAuditResult,
    summary="Audit component or screen against WCAG 2.1 AA standards",
)
def post_run_accessibility_audit(
    payload: AccessibilityAuditRequest,
) -> AccessibilityAuditResult:
    """Evaluate touch targets, contrast, keyboard trapping, visible focus, and color independence."""
    return run_accessibility_audit(request=payload)


@router.get(
    "/interaction/qa-matrix",
    response_model=list[VisualQASpecContract],
    summary="List automated visual regression QA test specifications",
)
def get_visual_qa_matrix() -> list[VisualQASpecContract]:
    """Retrieve master catalog of visual regression fixtures across viewports and states."""
    return list_visual_qa_fixtures()


# ---------------------------------------------------------------------------
# Production Release & Integration Endpoints (Phase 16 - FINAL)
# ---------------------------------------------------------------------------

from schemas.visual.release import (
    EndToEndJourneySpecContract,
    GoldenArtifactContract,
    NavigationRegistryEntryContract,
    ProductionReleaseReportContract,
    ScreenRegistryEntryContract,
    TokenValidationReportContract,
    TokenValidationRequestContract,
    VisualChecklistItemContract,
    VisualReleaseGateAuditRequest,
    VisualTrackStatusContract,
)
from .release_service import (
    get_e2e_journeys,
    get_golden_artifacts,
    get_navigation_registry,
    get_screen_registry,
    get_visual_quality_checklist,
    get_visual_track_completion_status,
    run_production_release_gate,
    validate_token_reference,
)


@router.get(
    "/release/screens",
    response_model=list[ScreenRegistryEntryContract],
    summary="Retrieve canonical screen registry with routing and dependencies",
)
def get_release_screens() -> list[ScreenRegistryEntryContract]:
    """Retrieve production screen registry with routes, templates, features, and dependencies."""
    return get_screen_registry()


@router.get(
    "/release/navigation",
    response_model=list[NavigationRegistryEntryContract],
    summary="Retrieve unified production navigation registry",
)
def get_release_navigation() -> list[NavigationRegistryEntryContract]:
    """Retrieve centralized navigation registry mapping routes to screens and permission groups."""
    return get_navigation_registry()


@router.post(
    "/release/token-validation",
    response_model=TokenValidationReportContract,
    summary="Validate token references against rogue values and broken hierarchies",
)
def post_validate_token(payload: TokenValidationRequestContract) -> TokenValidationReportContract:
    """Validate design token hierarchy (Screen -> Component -> Semantic -> Primitive)."""
    return validate_token_reference(request=payload)


@router.post(
    "/release/gate-audit",
    response_model=ProductionReleaseReportContract,
    summary="Execute comprehensive 5-gate production release audit",
)
def post_release_gate_audit(payload: VisualReleaseGateAuditRequest) -> ProductionReleaseReportContract:
    """Audit functional, visual, accessibility, performance, and integration gates for release."""
    return run_production_release_gate(request=payload)


@router.get(
    "/release/checklist",
    response_model=list[VisualChecklistItemContract],
    summary="Retrieve Master Visual Quality Checklist across 13 categories",
)
def get_release_checklist() -> list[VisualChecklistItemContract]:
    """Retrieve complete production quality checklist covering Foundation through QA."""
    return get_visual_quality_checklist()


@router.get(
    "/release/e2e-journeys",
    response_model=list[EndToEndJourneySpecContract],
    summary="Retrieve specifications and status for Master E2E User Journeys",
)
def get_release_e2e_journeys() -> list[EndToEndJourneySpecContract]:
    """Retrieve verified E2E user journeys (E2E-001 through E2E-005)."""
    return get_e2e_journeys()


@router.get(
    "/release/golden-artifacts",
    response_model=list[GoldenArtifactContract],
    summary="Retrieve 15 Golden Screens and 15 Golden Components regression anchors",
)
def get_release_golden_artifacts() -> list[GoldenArtifactContract]:
    """Retrieve golden regression targets and allowed match thresholds."""
    return get_golden_artifacts()


@router.get(
    "/release/status",
    response_model=VisualTrackStatusContract,
    summary="Retrieve master completion status of the entire VD-00 through VD-16 Track",
)
def get_release_track_status() -> VisualTrackStatusContract:
    """Retrieve track completion metrics and final handoff status declaration."""
    return get_visual_track_completion_status()










