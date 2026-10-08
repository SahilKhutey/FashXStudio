from decimal import Decimal
from uuid import uuid4

from fastapi.testclient import TestClient

from fashx.api.v1.returns import router
from fashx.main import app

client = TestClient(app)


def test_returns_router_exists():
    routes = {route.path for route in router.routes}
    assert "/returns" in routes
    assert "/returns/cancellations" in routes
    assert "/returns/refunds" in routes


def test_create_return_api():
    order_id = str(uuid4())
    customer_id = str(uuid4())
    order_line_id = str(uuid4())
    product_id = str(uuid4())

    response = client.post(
        "/api/v1/returns",
        json={
            "order_id": order_id,
            "customer_id": customer_id,
            "reason": "defective",
            "notes": "Defective zipper",
            "lines": [
                {
                    "order_line_id": order_line_id,
                    "product_id": product_id,
                    "quantity": 1,
                    "refund_amount": "899.50",
                }
            ],
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["order_id"] == order_id
    assert data["status"] == "requested"
    assert "id" in data


def test_create_cancellation_api():
    order_id = str(uuid4())
    customer_id = str(uuid4())

    response = client.post(
        "/api/v1/returns/cancellations",
        json={
            "order_id": order_id,
            "customer_id": customer_id,
            "reason": "Changed mind before shipping",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["order_id"] == order_id
    assert data["status"] == "requested"
    assert "id" in data


def test_create_refund_api():
    order_id = str(uuid4())

    response = client.post(
        "/api/v1/returns/refunds",
        json={
            "order_id": order_id,
            "amount": "450.00",
            "currency": "INR",
            "reason": "order_cancelled",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["order_id"] == order_id
    assert Decimal(str(data["amount"])) == Decimal("450.00")
    assert data["currency"] == "INR"
    assert data["status"] == "requested"
    assert "id" in data
