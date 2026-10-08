from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient

from fashx.core.bootstrap import register_core_services
from fashx.core.context import CoreContext
from fashx.core.runtime import get_core_runtime
from fashx.domain.fulfillment.enums import FulfillmentStatus
from fashx.main import app

client = TestClient(app)


def test_create_fulfillment_api() -> None:
    order_id = str(uuid4())
    order_line_id = str(uuid4())
    product_id = str(uuid4())

    response = client.post(
        "/api/v1/fulfillment",
        json={
            "order_id": order_id,
            "shipping_method": "standard",
            "address": {
                "recipient_name": "API Tester",
                "address_line_1": "100 Fashion Blvd",
                "city": "Mumbai",
                "state": "Maharashtra",
                "postal_code": "400001",
                "country": "IN",
            },
            "lines": [
                {
                    "order_line_id": order_line_id,
                    "product_id": product_id,
                    "quantity": 1,
                }
            ],
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["order_id"] == order_id
    assert data["status"] == "created"
    assert "id" in data


def test_create_shipment_api() -> None:
    order_id = str(uuid4())
    order_line_id = str(uuid4())
    product_id = str(uuid4())

    # 1. Create fulfillment
    create_resp = client.post(
        "/api/v1/fulfillment",
        json={
            "order_id": order_id,
            "shipping_method": "express",
            "address": {
                "recipient_name": "Express Customer",
                "address_line_1": "200 Fast Track",
                "city": "Delhi",
                "state": "Delhi",
                "postal_code": "110001",
                "country": "IN",
            },
            "lines": [
                {
                    "order_line_id": order_line_id,
                    "product_id": product_id,
                    "quantity": 2,
                }
            ],
        },
    )
    assert create_resp.status_code == 201
    fulfillment_id = create_resp.json()["id"]

    # 2. Advance status to PROCESSING via fulfillment service
    register_core_services()
    runtime = get_core_runtime()
    fulfillment_service = runtime.registry.get("fulfillment_service")

    import asyncio
    from uuid import UUID

    asyncio.run(
        fulfillment_service.change_fulfillment_status(
            context=CoreContext.create(),
            fulfillment_id=UUID(fulfillment_id),
            target=FulfillmentStatus.PROCESSING,
        )
    )

    # 3. Create shipment
    ship_resp = client.post(
        f"/api/v1/fulfillment/{fulfillment_id}/shipments",
        json={
            "carrier": "BlueDart",
            "shipping_method": "express",
        },
    )
    assert ship_resp.status_code == 201
    ship_data = ship_resp.json()
    assert ship_data["fulfillment_id"] == fulfillment_id
    assert ship_data["carrier"] == "BlueDart"
    assert ship_data["status"] == "label_created"
    assert ship_data["tracking_number"] is not None
