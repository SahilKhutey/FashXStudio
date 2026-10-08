from uuid import uuid4

from fastapi.testclient import TestClient

from fashx.api.v1.customer import router
from app.main import app

client = TestClient(app)


def test_customer_router_exists():
    routes = {route.path for route in router.routes}
    assert "/customers" in routes
    assert "/customers/{customer_id}" in routes
    assert "/customers/{customer_id}/addresses" in routes
    assert "/customers/{customer_id}/preferences" in routes


def test_create_and_get_customer_api():
    email = f"api_user_{uuid4().hex[:8]}@example.com"
    response = client.post(
        "/api/v1/customers",
        json={
            "email": email,
            "first_name": "API",
            "last_name": "User",
            "phone": "+919876543210",
        },
    )
    assert response.status_code == 201
    data = response.json()
    customer_id = data["id"]
    assert data["email"] == email
    assert data["first_name"] == "API"
    assert data["last_name"] == "User"
    assert data["status"] == "active"

    # Get customer
    get_res = client.get(f"/api/v1/customers/{customer_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == customer_id


def test_update_customer_api():
    email = f"update_{uuid4().hex[:8]}@example.com"
    create_res = client.post(
        "/api/v1/customers",
        json={
            "email": email,
            "first_name": "Before",
            "last_name": "Change",
        },
    )
    customer_id = create_res.json()["id"]

    patch_res = client.patch(
        f"/api/v1/customers/{customer_id}",
        json={
            "first_name": "After",
            "phone": "+919988776655",
        },
    )
    assert patch_res.status_code == 200
    updated_data = patch_res.json()
    assert updated_data["first_name"] == "After"
    assert updated_data["last_name"] == "Change"
    assert updated_data["phone"] == "+919988776655"


def test_add_and_list_address_api():
    email = f"addr_{uuid4().hex[:8]}@example.com"
    create_res = client.post(
        "/api/v1/customers",
        json={"email": email},
    )
    customer_id = create_res.json()["id"]

    addr_res = client.post(
        f"/api/v1/customers/{customer_id}/addresses",
        json={
            "address_type": "home",
            "recipient_name": "John Doe",
            "address_line_1": "Flat 101, Palm Grove",
            "city": "Bengaluru",
            "state": "Karnataka",
            "postal_code": "560001",
            "country": "IN",
        },
    )
    assert addr_res.status_code == 201
    addr_data = addr_res.json()
    assert addr_data["customer_id"] == customer_id
    assert addr_data["city"] == "Bengaluru"
    assert addr_data["is_default"] is True
    assert addr_data["status"] == "active"

    # List addresses
    list_res = client.get(f"/api/v1/customers/{customer_id}/addresses")
    assert list_res.status_code == 200
    items = list_res.json()
    assert len(items) == 1
    assert items[0]["id"] == addr_data["id"]


def test_set_preference_api():
    email = f"pref_{uuid4().hex[:8]}@example.com"
    create_res = client.post(
        "/api/v1/customers",
        json={"email": email},
    )
    customer_id = create_res.json()["id"]

    pref_res = client.post(
        f"/api/v1/customers/{customer_id}/preferences",
        json={
            "scope": "commerce",
            "key": "currency",
            "value": "INR",
        },
    )
    assert pref_res.status_code == 201
    pref_data = pref_res.json()
    assert pref_data["customer_id"] == customer_id
    assert pref_data["scope"] == "commerce"
    assert pref_data["key"] == "currency"
    assert pref_data["value"] == "INR"
