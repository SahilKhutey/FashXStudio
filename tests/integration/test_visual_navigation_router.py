"""Integration tests for Navigation System REST API endpoints — Phase 04."""

from fastapi.testclient import TestClient
from api.app.main import app

client = TestClient(app)


def test_get_nav_registry() -> None:
    """GET /api/v1/visual/navigation/registry returns primary + personal routes."""
    res = client.get("/api/v1/visual/navigation/registry")
    assert res.status_code == 200
    data = res.json()
    primary = [r for r in data["routes"] if r["group"] == "primary"]
    personal = [r for r in data["routes"] if r["group"] == "personal"]
    assert len(primary) == 9
    assert len(personal) == 3


def test_get_nav_registry_has_nested_children() -> None:
    """Shopping and Style items in registry have nested children."""
    res = client.get("/api/v1/visual/navigation/registry")
    data = res.json()
    shopping = next(r for r in data["routes"] if r["id"] == "nav-shopping")
    assert len(shopping["children"]) >= 4
    style = next(r for r in data["routes"] if r["id"] == "nav-style")
    assert len(style["children"]) >= 5


def test_resolve_navigation_mobile() -> None:
    """GET /api/v1/visual/navigation/resolve for mobile returns mobile_header."""
    res = client.get(
        "/api/v1/visual/navigation/resolve?route=/discover&viewport_width=375"
    )
    assert res.status_code == 200
    data = res.json()
    assert data["navigation_state"]["presentation"] == "mobile_header"
    assert data["active_item"]["id"] == "nav-discover"


def test_resolve_navigation_desktop_expanded() -> None:
    """GET /api/v1/visual/navigation/resolve for desktop returns desktop_expanded."""
    res = client.get(
        "/api/v1/visual/navigation/resolve?route=/fashion&viewport_width=1440"
    )
    assert res.status_code == 200
    data = res.json()
    assert data["navigation_state"]["presentation"] == "desktop_expanded"
    assert data["active_item"]["id"] == "nav-fashion"


def test_resolve_navigation_nested_child() -> None:
    """GET /api/v1/visual/navigation/resolve for nested child sets active + parent."""
    res = client.get(
        "/api/v1/visual/navigation/resolve?route=/shopping/products&viewport_width=1440"
    )
    assert res.status_code == 200
    data = res.json()
    assert data["active_item"]["id"] == "nav-shopping-products"
    assert data["active_parent"]["id"] == "nav-shopping"


def test_get_nav_breadcrumbs_shallow() -> None:
    """GET /api/v1/visual/navigation/breadcrumbs for /discover returns 2-entry chain."""
    res = client.get("/api/v1/visual/navigation/breadcrumbs?route=/discover")
    assert res.status_code == 200
    data = res.json()
    assert len(data["entries"]) == 2
    assert data["entries"][-1]["is_current"] is True
    assert data["entries"][-1]["is_interactive"] is False
    assert data["mobile_label"] == "Home"


def test_get_nav_breadcrumbs_deep() -> None:
    """GET /api/v1/visual/navigation/breadcrumbs for /shopping/products returns 3-entry chain."""
    res = client.get("/api/v1/visual/navigation/breadcrumbs?route=/shopping/products")
    assert res.status_code == 200
    data = res.json()
    labels = [e["label"] for e in data["entries"]]
    assert labels == ["Home", "Shopping", "Products"]
    assert data["mobile_label"] == "Shopping"


def test_get_nav_guards_unauthenticated() -> None:
    """GET /api/v1/visual/navigation/guards for unauthenticated user restricts auth items."""
    res = client.get("/api/v1/visual/navigation/guards?is_authenticated=false")
    assert res.status_code == 200
    guards = res.json()
    restricted = [g for g in guards if g["visibility"] == "restricted"]
    assert len(restricted) > 0  # saved, wishlist, profile, cart, orders are restricted


def test_get_nav_guards_authenticated() -> None:
    """GET /api/v1/visual/navigation/guards for authenticated user shows all items."""
    res = client.get("/api/v1/visual/navigation/guards?is_authenticated=true")
    assert res.status_code == 200
    guards = res.json()
    restricted = [g for g in guards if g["visibility"] == "restricted"]
    assert len(restricted) == 0


def test_get_product_tabs() -> None:
    """GET /api/v1/visual/navigation/tabs/product returns 4 tabs with active state."""
    res = client.get(
        "/api/v1/visual/navigation/tabs/product?product_id=abc123&active_route=/products/abc123/reviews"
    )
    assert res.status_code == 200
    data = res.json()
    assert len(data["tabs"]) == 4
    active_tabs = [t for t in data["tabs"] if t["is_active"]]
    assert len(active_tabs) == 1
    assert active_tabs[0]["id"] == "tab-reviews"


def test_get_context_navigation_profile() -> None:
    """GET /api/v1/visual/navigation/context for profile marks correct active item."""
    res = client.get(
        "/api/v1/visual/navigation/context?context_id=profile-context-nav&active_route=/profile/saved"
    )
    assert res.status_code == 200
    data = res.json()
    assert data["context_id"] == "profile-context-nav"
    active = [i for i in data["items"] if i["is_active"]]
    assert len(active) == 1
    assert active[0]["route"] == "/profile/saved"


def test_get_context_navigation_unknown() -> None:
    """GET /api/v1/visual/navigation/context for unknown context returns 404."""
    res = client.get(
        "/api/v1/visual/navigation/context?context_id=nonexistent-context"
    )
    assert res.status_code == 404


def test_get_nav_404_error() -> None:
    """GET /api/v1/visual/navigation/error/404 returns correct error contract."""
    res = client.get("/api/v1/visual/navigation/error/404?route=/bad-route")
    assert res.status_code == 200
    data = res.json()
    assert data["error_code"] == "not_found"
    assert data["attempted_route"] == "/bad-route"
    assert data["primary_recovery_route"] == "/"
    assert data["secondary_recovery_route"] == "/discover"


def test_get_nav_data_failure_error() -> None:
    """GET /api/v1/visual/navigation/error/data-failure returns Try Again recovery."""
    res = client.get(
        "/api/v1/visual/navigation/error/data-failure?route=/fashion/123"
    )
    assert res.status_code == 200
    data = res.json()
    assert data["error_code"] == "data_failure"
    assert data["primary_recovery_route"] == "/fashion/123"
