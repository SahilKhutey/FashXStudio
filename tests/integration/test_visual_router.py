"""Integration tests for Visual Layer endpoints.

Verifies HTTP routing, listing, filtering, schema serialization,
and RFC-7807 error envelopes for Screen Inventory, Templates, and Breakpoints.
"""

from fastapi.testclient import TestClient

from fashx.main import app

client = TestClient(app)


def test_get_screens_full_inventory() -> None:
    response = client.get("/api/v1/visual/screens")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == "1.0.0"
    assert data["total_screens"] == 123
    assert len(data["screens"]) == 123


def test_filter_screens_by_domain() -> None:
    response = client.get("/api/v1/visual/screens?domain=product")
    assert response.status_code == 200
    data = response.json()
    assert data["total_screens"] == 10
    for screen in data["screens"]:
        assert screen["domain"] == "product"


def test_filter_screens_by_template() -> None:
    response = client.get("/api/v1/visual/screens?template_type=detail")
    assert response.status_code == 200
    data = response.json()
    assert data["total_screens"] == 14
    for screen in data["screens"]:
        assert screen["template_type"] == "detail"


def test_filter_screens_by_dependency_group() -> None:
    response = client.get("/api/v1/visual/screens?dependency_group=group_a_foundation")
    assert response.status_code == 200
    data = response.json()
    assert data["total_screens"] == 8
    for screen in data["screens"]:
        assert screen["dependency_group"] == "group_a_foundation"


def test_get_screen_by_id_success() -> None:
    response = client.get("/api/v1/visual/screens/P02")
    assert response.status_code == 200
    screen = response.json()
    assert screen["screen_id"] == "P02"
    assert screen["title"] == "Product Detail"
    assert screen["template_type"] == "detail"


def test_get_screen_by_id_not_found() -> None:
    response = client.get("/api/v1/visual/screens/SCR-NONEXISTENT")
    assert response.status_code == 404
    error = response.json()["error"]
    assert error["code"] == "entity_not_found"
    assert "SCR-NONEXISTENT" in error["message"]


def test_get_breakpoints() -> None:
    response = client.get("/api/v1/visual/breakpoints")
    assert response.status_code == 200
    breakpoints = response.json()
    assert len(breakpoints) == 5
    bps = [b["breakpoint"] for b in breakpoints]
    assert bps == ["xs", "sm", "md", "lg", "xl"]


def test_get_domains_summary() -> None:
    response = client.get("/api/v1/visual/domains")
    assert response.status_code == 200
    summary = response.json()
    assert len(summary) == 13
    assert summary["platform"] == 8
    assert summary["home"] == 7
    assert summary["discovery"] == 10
    assert summary["search"] == 10
    assert summary["product"] == 10
    assert summary["shopping"] == 12
    assert summary["fashion"] == 9
    assert summary["style"] == 9
    assert summary["trends"] == 8
    assert summary["regional"] == 10
    assert summary["ai"] == 9
    assert summary["profile"] == 11
    assert summary["system"] == 10


def test_get_templates_summary() -> None:
    response = client.get("/api/v1/visual/templates")
    assert response.status_code == 200
    summary = response.json()
    assert len(summary) == 11
    assert summary["listing"] == 32
    assert summary["dashboard"] == 18
    assert summary["settings"] == 16
    assert summary["discovery"] == 15
    assert summary["detail"] == 14
    assert summary["editorial"] == 8
    assert summary["map"] == 7
    assert summary["assistant"] == 5
    assert summary["checkout"] == 4
    assert summary["builder"] == 3
    assert summary["comparison"] == 1


def test_get_dependency_groups_summary() -> None:
    response = client.get("/api/v1/visual/dependency-groups")
    assert response.status_code == 200
    summary = response.json()
    assert len(summary) == 5
    assert summary["group_a_foundation"] == 8
    assert summary["group_b_core_content"] == 46
    assert summary["group_c_advanced_experiences"] == 48
    assert summary["group_d_personalization"] == 11
    assert summary["group_e_production_quality"] == 10
