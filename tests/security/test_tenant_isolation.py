import base64
from fastapi.testclient import TestClient

from fashx.main import create_app


def get_client() -> TestClient:
    app = create_app()
    return TestClient(app)


def test_unauthenticated_widget_session_request_fails():
    client = get_client()
    resp = client.post(
        "/widget/v1/session",
        json={"external_product_id": "shopify_prod_99182"},
    )
    assert resp.status_code == 401
    assert "Invalid or missing X-FashX-Key" in resp.json()["detail"]


def test_valid_api_key_creates_widget_session():
    client = get_client()
    resp = client.post(
        "/widget/v1/session",
        headers={"X-FashX-Key": "test_partner_key_hash"},
        json={"external_product_id": "shopify_prod_99182", "category": "kurta"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "session_token" in data
    assert data["session_token"].startswith("sess_")
    assert data["tenant_name"] == "House of Indya"
    assert "24h" in data["ephemeral_guarantee"]


def test_tryon_without_valid_session_fails():
    client = get_client()
    resp = client.post(
        "/widget/v1/tryon",
        json={
            "session_token": "non_existent_session",
            "external_product_id": "prod_1",
            "size": "M",
            "photo_base64": "dummy",
        },
    )
    assert resp.status_code == 404


def test_tryon_with_valid_session_and_photo_succeeds():
    client = get_client()
    # 1. Create session
    s_resp = client.post(
        "/widget/v1/session",
        headers={"X-FashX-Key": "test_partner_key_hash"},
        json={"external_product_id": "kurta_embroidered_01", "category": "kurta"},
    )
    session_token = s_resp.json()["session_token"]

    # 2. Submit tryon
    dummy_photo = base64.b64encode(b"valid_shopper_test_photo_bytes_long_enough_to_pass_validation").decode()
    resp = client.post(
        "/widget/v1/tryon",
        json={
            "session_token": session_token,
            "external_product_id": "kurta_embroidered_01",
            "size": "L",
            "photo_base64": dummy_photo,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "completed"
    assert "tryon_id" in data
    assert data["fit_recommendation"]["recommended_size"] == "L"
    assert data["fit_recommendation"]["fit_score"] >= 0.90


def test_tryon_session_rate_limit_enforced():
    client = get_client()
    s_resp = client.post(
        "/widget/v1/session",
        headers={"X-FashX-Key": "test_partner_key_hash"},
        json={"external_product_id": "kurta_embroidered_01"},
    )
    session_token = s_resp.json()["session_token"]
    dummy_photo = base64.b64encode(b"valid_shopper_test_photo_bytes_long_enough_to_pass_validation").decode()

    # Exhaust rate limit of 10
    for i in range(10):
        r = client.post(
            "/widget/v1/tryon",
            json={
                "session_token": session_token,
                "external_product_id": "kurta_embroidered_01",
                "size": "M",
                "photo_base64": dummy_photo,
            },
        )
        assert r.status_code == 200

    # 11th must fail with 429
    r11 = client.post(
        "/widget/v1/tryon",
        json={
            "session_token": session_token,
            "external_product_id": "kurta_embroidered_01",
            "size": "M",
            "photo_base64": dummy_photo,
        },
    )
    assert r11.status_code == 429
    assert "Session try-on limit reached" in r11.json()["detail"]


def test_merchant_dashboard_access_control():
    client = get_client()
    # Unauthenticated fails
    resp_unauth = client.get("/merchant/dashboard")
    assert resp_unauth.status_code == 401

    # Authenticated succeeds
    resp_auth = client.get("/merchant/dashboard", headers={"X-FashX-Key": "live_key_secret"})
    assert resp_auth.status_code == 200
    data = resp_auth.json()
    assert data["tenant_name"] == "House of Indya"
    assert data["summary"]["return_reduction_pts"] >= 3.0
    assert data["summary"]["estimated_cost_savings_inr"] > 100000.0


def test_merchant_analytics_funnel():
    client = get_client()
    resp = client.get("/merchant/analytics", headers={"X-FashX-Key": "live_key_secret"})
    assert resp.status_code == 200
    data = resp.json()
    assert "funnel" in data
    assert data["funnel"]["modal_open_rate_pct"] > 10.0
    assert "categories" in data
    assert "kurtas" in data["categories"]
