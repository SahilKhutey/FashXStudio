from uuid import uuid4

from fastapi.testclient import TestClient

from fashx.main import app

client = TestClient(app)


def test_create_location():
    response = client.post(
        "/api/v1/inventory/locations",
        json={
            "name": "Main Warehouse",
            "code": f"WH-{uuid4().hex[:6]}",
            "location_type": "warehouse",
        },
    )

    assert response.status_code == 201

    data = response.json()
    assert data["name"] == "Main Warehouse"
    assert "code" in data
    assert data["location_type"] == "warehouse"


def test_create_inventory():
    code = f"WH-{uuid4().hex[:6]}"
    location_response = client.post(
        "/api/v1/inventory/locations",
        json={
            "name": "Warehouse API",
            "code": code,
        },
    )
    assert location_response.status_code == 201
    location_id = location_response.json()["id"]

    variant_id = str(uuid4())
    response = client.post(
        "/api/v1/inventory/items",
        json={
            "variant_id": variant_id,
            "location_id": location_id,
            "on_hand": 50,
            "incoming": 20,
        },
    )

    assert response.status_code == 201
    data = response.json()

    assert data["on_hand"] == 50
    assert data["reserved"] == 0
    assert data["available"] == 50
    assert data["incoming"] == 20
    assert data["status"] == "draft"
    assert data["availability"] == "unavailable"


def test_get_inventory_and_variant_list():
    code = f"WH-{uuid4().hex[:6]}"
    loc_resp = client.post(
        "/api/v1/inventory/locations",
        json={"name": "Loc Variant", "code": code},
    )
    location_id = loc_resp.json()["id"]
    variant_id = str(uuid4())

    inv_resp = client.post(
        "/api/v1/inventory/items",
        json={
            "variant_id": variant_id,
            "location_id": location_id,
            "on_hand": 100,
        },
    )
    inv_id = inv_resp.json()["id"]

    get_resp = client.get(f"/api/v1/inventory/items/{inv_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == inv_id

    list_resp = client.get(f"/api/v1/inventory/variants/{variant_id}")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1


def test_adjust_and_status_api():
    code = f"WH-{uuid4().hex[:6]}"
    loc_resp = client.post(
        "/api/v1/inventory/locations",
        json={"name": "Loc Adjust", "code": code},
    )
    location_id = loc_resp.json()["id"]

    inv_resp = client.post(
        "/api/v1/inventory/items",
        json={
            "variant_id": str(uuid4()),
            "location_id": location_id,
            "on_hand": 20,
        },
    )
    inv_id = inv_resp.json()["id"]

    # Activate
    status_resp = client.post(
        f"/api/v1/inventory/items/{inv_id}/status",
        json={"status": "active"},
    )
    assert status_resp.status_code == 200
    assert status_resp.json()["status"] == "active"
    assert status_resp.json()["availability"] == "available"

    # Adjust - receive
    adj_resp = client.post(
        f"/api/v1/inventory/items/{inv_id}/adjust",
        json={"adjustment_type": "receive", "quantity": 10},
    )
    assert adj_resp.status_code == 200
    assert adj_resp.json()["on_hand"] == 30
    assert adj_resp.json()["available"] == 30

    # Adjust - remove
    adj_resp2 = client.post(
        f"/api/v1/inventory/items/{inv_id}/adjust",
        json={"adjustment_type": "remove", "quantity": 5},
    )
    assert adj_resp2.status_code == 200
    assert adj_resp2.json()["on_hand"] == 25
    assert adj_resp2.json()["available"] == 25
