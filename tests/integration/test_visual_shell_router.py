"""Integration tests for Application Shell REST API endpoints — Phase 03.

Tests shell resolution, navigation config, breadcrumbs, layout mode,
page header factory, and layout template endpoints.
"""

from fastapi.testclient import TestClient
from fashx.main import app

client = TestClient(app)


def test_get_shell_mobile() -> None:
    """GET /api/v1/visual/shell with mobile viewport returns mobile shell."""
    res = client.get("/api/v1/visual/shell?viewport_width=375&active_route=/discover")
    assert res.status_code == 200
    data = res.json()
    assert data["layout_mode"] == "mobile"
    assert data["sidebar_mode"] == "hidden"
    assert data["drawer_state"] == "closed"
    assert data["active_route"] == "/discover"
    assert data["load_state"] == "ready"


def test_get_shell_desktop() -> None:
    """GET /api/v1/visual/shell with desktop viewport returns expanded sidebar."""
    res = client.get("/api/v1/visual/shell?viewport_width=1440")
    assert res.status_code == 200
    data = res.json()
    assert data["layout_mode"] == "desktop"
    assert data["sidebar_mode"] == "expanded"


def test_get_shell_navigation_structure() -> None:
    """GET /api/v1/visual/shell/navigation returns 9 primary + 3 personal items."""
    res = client.get("/api/v1/visual/shell/navigation")
    assert res.status_code == 200
    data = res.json()
    assert len(data["primary"]) == 9
    assert len(data["personal"]) == 3
    primary_ids = [item["id"] for item in data["primary"]]
    assert "nav-home" in primary_ids
    assert "nav-ai" in primary_ids
    assert "nav-maps" in primary_ids


def test_get_breadcrumbs_root() -> None:
    """GET /api/v1/visual/shell/breadcrumbs?route=/ returns single Home crumb."""
    res = client.get("/api/v1/visual/shell/breadcrumbs?route=/")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["label"] == "Home"
    assert data[0]["is_current"] is True


def test_get_breadcrumbs_nested() -> None:
    """GET /api/v1/visual/shell/breadcrumbs?route=/shopping builds correct chain."""
    res = client.get("/api/v1/visual/shell/breadcrumbs?route=/shopping")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 2
    assert data[0]["label"] == "Home"
    assert data[0]["is_current"] is False
    assert data[1]["label"] == "Shopping"
    assert data[1]["is_current"] is True


def test_get_layout_mode() -> None:
    """GET /api/v1/visual/shell/layout-mode resolves mobile, tablet, desktop."""
    res_mobile = client.get("/api/v1/visual/shell/layout-mode?viewport_width=375")
    assert res_mobile.status_code == 200
    assert res_mobile.json()["layout_mode"] == "mobile"
    assert res_mobile.json()["sidebar_mode"] == "hidden"

    res_tablet = client.get("/api/v1/visual/shell/layout-mode?viewport_width=768")
    assert res_tablet.json()["layout_mode"] == "tablet"
    assert res_tablet.json()["sidebar_mode"] == "hidden"

    res_desktop = client.get("/api/v1/visual/shell/layout-mode?viewport_width=1440")
    assert res_desktop.json()["layout_mode"] == "desktop"
    assert res_desktop.json()["sidebar_mode"] == "expanded"


def test_get_page_header_standard() -> None:
    """GET /api/v1/visual/shell/page-header builds standard header with breadcrumbs."""
    res = client.get(
        "/api/v1/visual/shell/page-header?title=Discover+Fashion&route=/discover"
    )
    assert res.status_code == 200
    data = res.json()
    assert data["title"] == "Discover Fashion"
    assert data["variant"] == "standard"
    assert len(data["breadcrumbs"]) == 2
    assert data["breadcrumbs"][-1]["is_current"] is True


def test_get_page_header_listing_with_count() -> None:
    """GET /api/v1/visual/shell/page-header for listing variant includes result_count."""
    res = client.get(
        "/api/v1/visual/shell/page-header?title=Products&route=/shopping&variant=listing&result_count=256"
    )
    assert res.status_code == 200
    data = res.json()
    assert data["variant"] == "listing"
    assert data["result_count"] == 256


def test_get_layout_template_standard() -> None:
    """GET /api/v1/visual/shell/layout-template for standard is not full-bleed."""
    res = client.get("/api/v1/visual/shell/layout-template?template=standard")
    assert res.status_code == 200
    data = res.json()
    assert data["template"] == "standard"
    assert data["is_full_bleed"] is False
    assert data["scroll_behavior"] == "viewport"


def test_get_layout_template_editorial_is_full_bleed() -> None:
    """GET /api/v1/visual/shell/layout-template for editorial is full-bleed."""
    res = client.get("/api/v1/visual/shell/layout-template?template=editorial")
    assert res.status_code == 200
    assert res.json()["is_full_bleed"] is True


def test_get_layout_template_map_scroll_behavior() -> None:
    """GET /api/v1/visual/shell/layout-template for map uses feature-local scroll."""
    res = client.get("/api/v1/visual/shell/layout-template?template=map")
    assert res.status_code == 200
    assert res.json()["scroll_behavior"] == "feature-local"
