"""Unit tests for FashXStudio Application Shell System — Phase 03.

Validates navigation configuration, layout mode resolution, breadcrumb builder,
page header factories, overlay/toast management, and layout template contracts.
Enforces Constitution Rule I02 (Contract Primacy) with extra="forbid" models.
"""

import pytest
from schemas.visual.shell import (
    ApplicationShellContract,
    BreadcrumbItemContract,
    LayoutTemplate,
    LayoutTemplateContract,
    MobileDrawerState,
    NavigationGroup,
    NavigationItemContract,
    NavigationItemState,
    OverlayRegistryContract,
    OverlayType,
    PageHeaderContract,
    PageHeaderVariant,
    ShellLayoutMode,
    ShellLoadState,
    SidebarMode,
    ToastType,
)
from api.app.visual.shell_service import (
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


# ---------------------------------------------------------------------------
# 1. Navigation Configuration
# ---------------------------------------------------------------------------

def test_navigation_config_has_primary_and_personal() -> None:
    """Navigation config contains primary (9) and personal (3) items."""
    config = get_navigation_config()
    assert len(config.primary) == 9
    assert len(config.personal) == 3
    assert all(item.group == NavigationGroup.PRIMARY for item in config.primary)
    assert all(item.group == NavigationGroup.PERSONAL for item in config.personal)


def test_navigation_items_have_required_fields() -> None:
    """Every navigation item has id, label, icon, and route populated."""
    config = get_navigation_config()
    for item in config.primary + config.personal:
        assert item.id, f"Missing id on item {item}"
        assert item.label, f"Missing label on item {item}"
        assert item.icon, f"Missing icon on item {item}"
        assert item.route.startswith("/"), f"Route must start with '/': {item.route}"


def test_navigation_personal_items_require_auth() -> None:
    """All personal navigation items require authentication."""
    config = get_navigation_config()
    assert all(item.requires_auth for item in config.personal)


def test_navigation_primary_items_do_not_require_auth() -> None:
    """Primary navigation items are accessible without authentication."""
    config = get_navigation_config()
    assert all(not item.requires_auth for item in config.primary)


# ---------------------------------------------------------------------------
# 2. Layout Mode & Sidebar Resolution
# ---------------------------------------------------------------------------

def test_layout_mode_mobile() -> None:
    """Viewports under 768px resolve to MOBILE layout mode."""
    assert resolve_shell_layout_mode(375) == ShellLayoutMode.MOBILE
    assert resolve_shell_layout_mode(767) == ShellLayoutMode.MOBILE


def test_layout_mode_tablet() -> None:
    """Viewports 768–1023px resolve to TABLET layout mode."""
    assert resolve_shell_layout_mode(768) == ShellLayoutMode.TABLET
    assert resolve_shell_layout_mode(1023) == ShellLayoutMode.TABLET


def test_layout_mode_desktop() -> None:
    """Viewports >= 1024px resolve to DESKTOP layout mode."""
    assert resolve_shell_layout_mode(1024) == ShellLayoutMode.DESKTOP
    assert resolve_shell_layout_mode(1920) == ShellLayoutMode.DESKTOP


def test_sidebar_mode_resolution() -> None:
    """Sidebar collapses on tablet and hides on mobile."""
    assert resolve_sidebar_mode(1280) == SidebarMode.EXPANDED
    assert resolve_sidebar_mode(1024) == SidebarMode.COLLAPSED
    assert resolve_sidebar_mode(768) == SidebarMode.HIDDEN
    assert resolve_sidebar_mode(375) == SidebarMode.HIDDEN


# ---------------------------------------------------------------------------
# 3. Breadcrumb Builder
# ---------------------------------------------------------------------------

def test_breadcrumb_root_route() -> None:
    """Root route '/' returns single current breadcrumb 'Home'."""
    crumbs = resolve_breadcrumbs("/")
    assert len(crumbs) == 1
    assert crumbs[0].label == "Home"
    assert crumbs[0].is_current is True


def test_breadcrumb_nested_route() -> None:
    """Nested route builds correct breadcrumb chain."""
    crumbs = resolve_breadcrumbs("/shopping")
    assert len(crumbs) == 2
    assert crumbs[0].label == "Home"
    assert crumbs[0].is_current is False
    assert crumbs[1].label == "Shopping"
    assert crumbs[1].is_current is True


def test_breadcrumb_deep_route() -> None:
    """Deep routes correctly mark only the last segment as current."""
    crumbs = resolve_breadcrumbs("/shopping/products/123")
    assert crumbs[-1].is_current is True
    assert all(not c.is_current for c in crumbs[:-1])


# ---------------------------------------------------------------------------
# 4. Page Header Factory
# ---------------------------------------------------------------------------

def test_page_header_standard() -> None:
    """Standard page header has title, variant, and breadcrumbs."""
    header = build_page_header(title="Discover Fashion", route="/discover")
    assert header.title == "Discover Fashion"
    assert header.variant == PageHeaderVariant.STANDARD
    assert len(header.breadcrumbs) == 2
    assert header.breadcrumbs[-1].label == "Discover"


def test_page_header_listing_with_count() -> None:
    """Listing page header correctly carries result_count."""
    header = build_page_header(
        title="Products",
        variant=PageHeaderVariant.LISTING,
        result_count=342,
        route="/shopping",
    )
    assert header.variant == PageHeaderVariant.LISTING
    assert header.result_count == 342


# ---------------------------------------------------------------------------
# 5. Application Shell Factory
# ---------------------------------------------------------------------------

def test_application_shell_mobile() -> None:
    """Mobile viewport generates correct shell config."""
    shell = build_application_shell(viewport_width_px=375, active_route="/discover")
    assert shell.layout_mode == ShellLayoutMode.MOBILE
    assert shell.sidebar_mode == SidebarMode.HIDDEN
    assert shell.drawer_state == MobileDrawerState.CLOSED
    assert shell.active_route == "/discover"
    assert shell.load_state == ShellLoadState.READY


def test_application_shell_desktop() -> None:
    """Desktop viewport generates expanded sidebar and desktop layout."""
    shell = build_application_shell(viewport_width_px=1440, active_route="/")
    assert shell.layout_mode == ShellLayoutMode.DESKTOP
    assert shell.sidebar_mode == SidebarMode.EXPANDED


# ---------------------------------------------------------------------------
# 6. Layout Template Builder
# ---------------------------------------------------------------------------

def test_layout_template_standard() -> None:
    """Standard layout is not full-bleed and uses viewport scroll."""
    template = build_layout_template(LayoutTemplate.STANDARD)
    assert template.template == LayoutTemplate.STANDARD
    assert template.is_full_bleed is False
    assert template.scroll_behavior == "viewport"


def test_layout_template_editorial_is_full_bleed() -> None:
    """Editorial, Map, and Builder templates are full-bleed."""
    for t in [LayoutTemplate.EDITORIAL, LayoutTemplate.MAP, LayoutTemplate.BUILDER]:
        tmpl = build_layout_template(t)
        assert tmpl.is_full_bleed is True, f"{t} should be full-bleed"


def test_layout_template_map_uses_feature_local_scroll() -> None:
    """Map template uses feature-local scroll behavior."""
    template = build_layout_template(LayoutTemplate.MAP)
    assert template.scroll_behavior == "feature-local"


# ---------------------------------------------------------------------------
# 7. Overlay & Toast Service
# ---------------------------------------------------------------------------

def test_push_and_pop_overlay() -> None:
    """Overlay stack grows and shrinks correctly."""
    registry = OverlayRegistryContract()
    overlay = create_overlay("overlay-1", OverlayType.MODAL, title="Size Guide")
    registry = push_overlay(registry, overlay)
    assert len(registry.active_overlays) == 1
    assert registry.top_overlay is not None
    assert registry.top_overlay.overlay_id == "overlay-1"
    registry = pop_overlay(registry)
    assert len(registry.active_overlays) == 0
    assert registry.top_overlay is None


def test_push_and_dismiss_toast() -> None:
    """Toast queue grows and shrinks correctly."""
    registry = OverlayRegistryContract()
    toast = create_toast("t-1", "Product saved", ToastType.SUCCESS)
    registry = push_toast(registry, toast)
    assert len(registry.toast_queue) == 1
    assert registry.toast_queue[0].toast_type == ToastType.SUCCESS
    registry = dismiss_toast(registry, "t-1")
    assert len(registry.toast_queue) == 0


def test_overlay_focus_trap_default() -> None:
    """Overlays have focus trapping enabled by default."""
    overlay = create_overlay("o-drawer", OverlayType.DRAWER)
    assert overlay.has_focus_trap is True
    assert overlay.is_dismissible is True


def test_toast_auto_dismiss_default() -> None:
    """Toasts have 4000ms auto-dismiss by default."""
    toast = create_toast("t-info", "Some information")
    assert toast.auto_dismiss_ms == 4000
    assert toast.is_persistent is False
