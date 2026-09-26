from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.v1.checkout import router
from app.main import app

client = TestClient(app)


def test_checkout_router_exists():
    routes = {route.path for route in router.routes}
    assert "/checkout" in routes
    assert "/checkout/{checkout_id}/validate" in routes


def test_create_checkout_api():
    cart_id = str(uuid4())
    customer_id = str(uuid4())

    response = client.post(
        "/api/v1/checkout",
        json={
            "cart_id": cart_id,
            "customer_id": customer_id,
            "currency": "INR",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["cart_id"] == cart_id
    assert data["customer_id"] == customer_id
    assert data["status"] == "open"
    assert data["currency"] == "INR"
    assert "id" in data


def test_validate_checkout_api():
    cart_id = str(uuid4())
    create_res = client.post(
        "/api/v1/checkout",
        json={
            "cart_id": cart_id,
            "currency": "INR",
        },
    )
    assert create_res.status_code == 201
    checkout_id = create_res.json()["id"]

    val_res = client.post(f"/api/v1/checkout/{checkout_id}/validate")
    assert val_res.status_code == 200
    data = val_res.json()
    assert data["id"] == checkout_id
    assert data["status"] == "ready"


def test_validate_checkout_api_not_found():
    response = client.post(f"/api/v1/checkout/{uuid4()}/validate")
    assert response.status_code == 404
