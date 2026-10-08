from decimal import Decimal
from uuid import uuid4

from fastapi.testclient import TestClient

from fashx.api.v1.pricing import router
from fashx.main import app

client = TestClient(app)


def test_pricing_router_exists():
    routes = {route.path for route in router.routes}
    assert "/pricing/prices" in routes
    assert "/pricing/rules" in routes
    assert "/pricing/calculate" in routes


def test_create_price_api():
    product_id = str(uuid4())
    response = client.post(
        "/api/v1/pricing/prices",
        json={
            "product_id": product_id,
            "amount": "299.99",
            "currency": "INR",
            "price_type": "base",
            "status": "active",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert Decimal(str(data["amount"])) == Decimal("299.99")
    assert data["currency"] == "INR"
    assert data["status"] == "active"


def test_create_rule_api():
    response = client.post(
        "/api/v1/pricing/rules",
        json={
            "name": "Festival Sale",
            "product_id": str(uuid4()),
            "discount_type": "percentage",
            "discount_value": "15.00",
            "priority": 50,
            "status": "active",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["name"] == "Festival Sale"
    assert data["status"] == "active"


def test_calculate_api_end_to_end():
    product_id = str(uuid4())

    # 1. Create Price (1000.00 INR)
    price_res = client.post(
        "/api/v1/pricing/prices",
        json={
            "product_id": product_id,
            "amount": "1000.00",
            "currency": "INR",
            "price_type": "base",
            "status": "active",
        },
    )
    assert price_res.status_code == 201

    # 2. Create Rule (20% off for this product)
    rule_res = client.post(
        "/api/v1/pricing/rules",
        json={
            "name": "20% Off",
            "discount_type": "percentage",
            "discount_value": "20.00",
            "priority": 10,
            "product_id": product_id,
            "status": "active",
        },
    )
    assert rule_res.status_code == 201

    # 3. Calculate Price
    calc_res = client.post(
        "/api/v1/pricing/calculate",
        json={
            "product_id": product_id,
            "currency": "INR",
            "quantity": 2,
        },
    )
    assert calc_res.status_code == 200
    data = calc_res.json()
    # 1000 * 2 = 2000 original amount
    assert Decimal(data["original_amount"]) == Decimal("2000.00")
    # 20% of 2000 = 400 discount -> 1600 final amount
    assert Decimal(data["final_amount"]) == Decimal("1600.00")
    assert data["currency"] == "INR"
    assert len(data["adjustments"]) == 1
    assert data["adjustments"][0]["description"] == "20% Off"
    assert Decimal(data["adjustments"][0]["amount"]) == Decimal("-400.00")


def test_calculate_api_not_found():
    calc_res = client.post(
        "/api/v1/pricing/calculate",
        json={
            "product_id": str(uuid4()),
            "currency": "INR",
            "quantity": 1,
        },
    )
    assert calc_res.status_code == 404
