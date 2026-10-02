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





