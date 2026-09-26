from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_create_customer_with_number_and_display_name():
    email = f"core16_{uuid4().hex[:8]}@example.com"
    response = client.post(
        "/api/v1/customers",
        json={
            "email": email,
            "first_name": "Dev",
            "last_name": "User",
            "display_name": "DevU",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["customer_number"].startswith("FX-CUST-")
    assert data["display_name"] == "DevU"
    assert data["email"] == email


def test_put_customer_preferences_api():
    email = f"core16_prefs_{uuid4().hex[:8]}@example.com"
    create_res = client.post(
        "/api/v1/customers",
        json={"email": email, "first_name": "Ananya"},
    )
    assert create_res.status_code == 201
    cid = create_res.json()["id"]

    put_res = client.put(
        f"/api/v1/customers/{cid}/preferences",
        json={
            "preferred_currency": "USD",
            "preferred_region": "US-CA",
            "language": "en",
            "timezone": "America/Los_Angeles",
            "categories": ["streetwear", "outerwear"],
            "brands": ["Stussy", "Nike"],
            "styles": ["casual"],
            "sizes": {"tops": "L", "bottoms": "32"},
        },
    )
    assert put_res.status_code == 200
    pref_data = put_res.json()
    assert pref_data["customer_id"] == cid
    assert pref_data["preferred_currency"] == "USD"
    assert "streetwear" in pref_data["categories"]
    assert pref_data["sizes"]["tops"] == "L"


def test_post_customer_consent_api():
    email = f"core16_consent_{uuid4().hex[:8]}@example.com"
    create_res = client.post(
        "/api/v1/customers",
        json={"email": email, "first_name": "Kabir"},
    )
    assert create_res.status_code == 201
    cid = create_res.json()["id"]

    consent_res = client.post(
        f"/api/v1/customers/{cid}/consents",
        json={
            "consent_type": "personalization",
            "granted": True,
            "version": "1.0",
        },
    )
    assert consent_res.status_code == 201
    consent_data = consent_res.json()
    assert consent_data["customer_id"] == cid
    assert consent_data["consent_type"] == "personalization"
    assert consent_data["granted"] is True
    assert consent_data["version"] == "1.0"


def test_preferences_customer_not_found_api():
    random_id = str(uuid4())
    res = client.put(
        f"/api/v1/customers/{random_id}/preferences",
        json={"preferred_currency": "INR"},
    )
    assert res.status_code == 404


def test_consent_customer_not_found_api():
    random_id = str(uuid4())
    res = client.post(
        f"/api/v1/customers/{random_id}/consents",
        json={"consent_type": "privacy", "granted": True},
    )
    assert res.status_code == 404
