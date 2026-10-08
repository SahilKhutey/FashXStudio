from uuid import uuid4

from fastapi.testclient import TestClient

from fashx.main import app

client = TestClient(app)


def test_create_promotion():
    code = f"FEST-{uuid4().hex[:6]}"
    response = client.post(
        "/api/v1/promotions",
        json={
            "name": "Festival Sale",
            "code": code,
            "scope": "product",
            "discount_type": "percentage",
            "discount_value": "20",
        },
    )

    assert response.status_code == 201

    data = response.json()
    assert data["name"] == "Festival Sale"
    assert data["discount_value"] == "20"
    assert data["status"] == "draft"


def test_create_offer_and_calculate_api():
    code = f"PROMO-{uuid4().hex[:6]}"
    promo_resp = client.post(
        "/api/v1/promotions",
        json={
            "name": "Offer Test Promo",
            "code": code,
            "scope": "product",
            "discount_type": "percentage",
            "discount_value": "15",
        },
    )
    assert promo_resp.status_code == 201
    promo_id = promo_resp.json()["id"]

    # Activate promotion
    act_promo = client.post(
        f"/api/v1/promotions/{promo_id}/status",
        json={"status": "active"},
    )
    assert act_promo.status_code == 200
    assert act_promo.json()["status"] == "active"

    # Create offer
    product_id = str(uuid4())
    offer_resp = client.post(
        "/api/v1/promotions/offers",
        json={
            "promotion_id": promo_id,
            "product_id": product_id,
        },
    )
    assert offer_resp.status_code == 201
    offer_id = offer_resp.json()["id"]

    # Activate offer
    act_offer = client.post(
        f"/api/v1/promotions/offers/{offer_id}/status",
        json={"status": "active"},
    )
    assert act_offer.status_code == 200
    assert act_offer.json()["status"] == "active"

    # Calculate offer
    calc_resp = client.post(
        f"/api/v1/promotions/offers/{offer_id}/calculate",
        json={
            "amount": "1000",
            "currency": "INR",
        },
    )
    assert calc_resp.status_code == 200
    calc_data = calc_resp.json()
    assert calc_data["base_price_amount"] == "1000.00"
    assert calc_data["discount_amount"] == "150.00"
    assert calc_data["final_price_amount"] == "850.00"
