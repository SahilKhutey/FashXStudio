from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient

from fashx.main import app

client = TestClient(app)


def test_create_anonymous_cart_api() -> None:
    session_id = f"guest-{uuid4().hex[:8]}"
    response = client.post(
        "/api/v1/cart",
        json={
            "owner_type": "anonymous",
            "session_id": session_id,
            "currency": "USD",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["session_id"] == session_id
    assert data["owner_type"] == "anonymous"
    assert data["currency"] == "USD"
    assert data["status"] == "active"
    assert "id" in data


def test_create_customer_cart_api() -> None:
    customer_id = str(uuid4())
    response = client.post(
        "/api/v1/cart",
        json={
            "owner_type": "customer",
            "customer_id": customer_id,
            "currency": "EUR",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["customer_id"] == customer_id
    assert data["owner_type"] == "customer"
    assert data["currency"] == "EUR"


def test_get_cart_api() -> None:
    session_id = f"guest-{uuid4().hex[:8]}"
    create_resp = client.post(
        "/api/v1/cart",
        json={
            "owner_type": "anonymous",
            "session_id": session_id,
            "currency": "USD",
        },
    )
    assert create_resp.status_code == 201
    cart_id = create_resp.json()["id"]

    get_resp = client.get(f"/api/v1/cart/{cart_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == cart_id


def test_cart_lines_flow_api() -> None:
    session_id = f"guest-{uuid4().hex[:8]}"
    create_resp = client.post(
        "/api/v1/cart",
        json={
            "owner_type": "anonymous",
            "session_id": session_id,
            "currency": "USD",
        },
    )
    cart_id = create_resp.json()["id"]

    product_id = str(uuid4())
    listing_id = str(uuid4())

    # Add line 1
    add_resp = client.post(
        f"/api/v1/cart/{cart_id}/lines",
        json={
            "product_id": product_id,
            "listing_id": listing_id,
            "unit_price": "29.99",
            "currency": "USD",
            "quantity": 2,
        },
    )
    assert add_resp.status_code == 201
    line1 = add_resp.json()
    line1_id = line1["id"]
    assert line1["quantity"] == 2
    assert line1["unit_price"] == "29.99"

    # Add same product & listing -> should merge quantity
    merge_resp = client.post(
        f"/api/v1/cart/{cart_id}/lines",
        json={
            "product_id": product_id,
            "listing_id": listing_id,
            "unit_price": "29.99",
            "currency": "USD",
            "quantity": 3,
        },
    )
    assert merge_resp.status_code == 201
    merged = merge_resp.json()
    assert merged["id"] == line1_id
    assert merged["quantity"] == 5

    # Check totals
    totals_resp = client.get(f"/api/v1/cart/{cart_id}/totals")
    assert totals_resp.status_code == 200
    totals_data = totals_resp.json()
    assert totals_data["item_count"] == 5
    assert totals_data["subtotal"] == "149.95"
    assert totals_data["currency"] == "USD"

    # Update quantity
    patch_resp = client.patch(
        f"/api/v1/cart/lines/{line1_id}",
        json={"quantity": 1},
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["quantity"] == 1

    totals_resp2 = client.get(f"/api/v1/cart/{cart_id}/totals")
    assert totals_resp2.json()["item_count"] == 1
    assert totals_resp2.json()["subtotal"] == "29.99"

    # Add line 2
    add_resp2 = client.post(
        f"/api/v1/cart/{cart_id}/lines",
        json={
            "product_id": str(uuid4()),
            "listing_id": str(uuid4()),
            "unit_price": "10.00",
            "currency": "USD",
            "quantity": 1,
        },
    )
    assert add_resp2.status_code == 201
    line2_id = add_resp2.json()["id"]

    # Remove line 2
    del_line_resp = client.delete(f"/api/v1/cart/lines/{line2_id}")
    assert del_line_resp.status_code == 200

    totals_resp3 = client.get(f"/api/v1/cart/{cart_id}/totals")
    assert totals_resp3.json()["item_count"] == 1
    assert totals_resp3.json()["subtotal"] == "29.99"

    # Clear cart
    clear_resp = client.delete(f"/api/v1/cart/{cart_id}/lines")
    assert clear_resp.status_code == 204

    totals_resp4 = client.get(f"/api/v1/cart/{cart_id}/totals")
    assert totals_resp4.json()["item_count"] == 0
    assert totals_resp4.json()["subtotal"] == "0"
