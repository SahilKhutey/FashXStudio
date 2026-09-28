"""Integration tests for Visual Layer endpoints.

Verifies HTTP routing, listing, filtering, schema serialization,
and RFC-7807 error envelopes for Screen Inventory and Breakpoints.
"""

from fastapi.testclient import TestClient

from api.app.main import app

client = TestClient(app)


def test_get_screens_full_inventory() -> None:
    response = client.get("/api/v1/visual/screens")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == "1.0.0"
    assert data["total_screens"] >= 50
    assert len(data["screens"]) == data["total_screens"]


def test_filter_screens_by_domain() -> None:
    response = client.get("/api/v1/visual/screens?domain=vto")
    assert response.status_code == 200
    data = response.json()
    assert data["total_screens"] == 5
    for screen in data["screens"]:
        assert screen["domain"] == "vto"


def test_get_screen_by_id_success() -> None:
    response = client.get("/api/v1/visual/screens/SCR-VTO-01")
    assert response.status_code == 200
    screen = response.json()
    assert screen["screen_id"] == "SCR-VTO-01"
    assert screen["title"] == "Virtual Fitting Canvas"
    assert screen["requires_biometric_consent"] is True


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
    assert len(summary) == 12
    assert summary["discovery"] >= 5
    assert summary["vto"] >= 5
    assert summary["onboarding"] >= 5
