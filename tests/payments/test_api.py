from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

from fastapi.testclient import TestClient

from app.core.bootstrap import register_core_services
from app.core.runtime import get_core_runtime
from app.domain.orders.entities import Order
from app.main import app

client = TestClient(app)


def test_payment_api_flow() -> None:
    register_core_services()
    runtime = get_core_runtime()
    order_repo = runtime.registry.get("order_repository")

    order_id = uuid4()
    order = Order(
        id=order_id,
        order_number="FXS-20260926-000099",
        checkout_id=uuid4(),
        cart_id=uuid4(),
        email="buyer@example.com",
        subtotal=Decimal("2500"),
        total=Decimal("2500"),
        currency="INR",
    )
    import asyncio

    asyncio.run(order_repo.save(order))

    # 1. Create payment
    create_resp = client.post(
        "/api/v1/payments",
        json={
            "order_id": str(order_id),
            "currency": "INR",
        },
    )
    assert create_resp.status_code == 201
    payment_data = create_resp.json()
    payment_id = payment_data["id"]
    assert payment_data["order_id"] == str(order_id)
    assert payment_data["amount"] == "2500.0" or payment_data["amount"] == "2500.00" or payment_data["amount"] == "2500"
    assert payment_data["status"] == "created"
    assert payment_data["currency"] == "INR"

    # 2. Authorize payment
    auth_resp = client.post(
        f"/api/v1/payments/{payment_id}/authorize",
        json={"payment_method": "upi"},
    )
    assert auth_resp.status_code == 200
    auth_data = auth_resp.json()
    assert auth_data["status"] == "authorized"

    # 3. Capture payment
    cap_resp = client.post(
        f"/api/v1/payments/{payment_id}/capture",
    )
    assert cap_resp.status_code == 200
    cap_data = cap_resp.json()
    assert cap_data["status"] == "captured"
