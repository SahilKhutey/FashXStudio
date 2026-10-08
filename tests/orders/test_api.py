import asyncio
from decimal import Decimal
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.v1.orders import router
from fashx.core.bootstrap import register_core_services
from fashx.core.runtime import get_core_runtime
from fashx.domain.order.entities import (
    Order,
    OrderAddressSnapshot,
    OrderLine,
)
from app.main import app

client = TestClient(app)


def test_orders_router_exists():
    routes = {route.path for route in router.routes}
    assert "/orders/{order_id}" in routes


def test_get_order_api():
    register_core_services()
    runtime = get_core_runtime()
    order_repo = runtime.registry.get("order_repository")
    line_repo = runtime.registry.get("order_line_repository")

    order_id = uuid4()
    order = Order(
        id=order_id,
        order_number="FX-API-ORDER-001",
        customer_id=uuid4(),
        currency="INR",
        shipping_address=OrderAddressSnapshot(
            recipient_name="API Customer",
            address_line_1="API Street 1",
            city="Bengaluru",
            state="Karnataka",
            postal_code="560001",
        ),
        shipping_total=Decimal("50.00"),
        tax_total=Decimal("25.00"),
    )

    line = OrderLine(
        order_id=order_id,
        product_id=uuid4(),
        title="Fashion Shirt",
        quantity=2,
        unit_price=Decimal("400.00"),
        discount=Decimal("50.00"),
    )
    line.validate()
    order.calculate_totals([line])

    asyncio.run(order_repo.save(order))
    asyncio.run(line_repo.save(line))

    response = client.get(f"/api/v1/orders/{order_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(order_id)
    assert data["order_number"] == "FX-API-ORDER-001"
    assert data["status"] == "pending"
    assert data["currency"] == "INR"
    assert Decimal(str(data["subtotal"])) == Decimal("800.00")
    assert Decimal(str(data["discount_total"])) == Decimal("50.00")
    assert Decimal(str(data["shipping_total"])) == Decimal("50.00")
    assert Decimal(str(data["tax_total"])) == Decimal("25.00")
    assert Decimal(str(data["grand_total"])) == Decimal("825.00")


def test_get_order_api_not_found():
    response = client.get(f"/api/v1/orders/{uuid4()}")
    assert response.status_code == 404
