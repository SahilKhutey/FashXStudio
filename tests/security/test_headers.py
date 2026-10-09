from unittest.mock import patch

from fastapi.testclient import TestClient

from fashx.main import app, create_app


def test_standard_security_headers():
    client = TestClient(app)
    res = client.get("/")
    assert res.status_code == 200

    headers = res.headers
    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert headers.get("X-Frame-Options") == "DENY"
    assert headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert "geolocation=()" in headers.get("Permissions-Policy", "")
    assert headers.get("X-XSS-Protection") == "1; mode=block"


def test_production_headers_and_docs_gating():
    with patch("fashx.core.settings.Settings.is_production", True):
        prod_app = create_app()
        client = TestClient(prod_app)

        # Standard root response in prod has HSTS and CSP
        res = client.get("/")
        assert res.status_code == 200
        assert "max-age=31536000" in res.headers.get("Strict-Transport-Security", "")
        assert res.headers.get("Content-Security-Policy") == "default-src 'self'"

        # Docs and OpenAPI are gated / removed in prod
        assert client.get("/docs").status_code == 404
        assert client.get("/redoc").status_code == 404
        assert client.get("/openapi.json").status_code == 404
