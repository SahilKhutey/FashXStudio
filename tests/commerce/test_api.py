from uuid import uuid4

from fastapi.testclient import TestClient

from fashx.main import app

client = TestClient(app)


def test_create_brand():

    response = client.post(
        "/api/v1/commerce/brands",
        json={
            "name": "API Brand",
            "slug": "api-brand",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "API Brand"


def test_create_seller():

    response = client.post(
        "/api/v1/commerce/sellers",
        json={
            "name": "API Seller",
            "slug": "api-seller",
            "seller_type": "retailer",
        },
    )

    assert response.status_code == 201


def test_create_marketplace():

    response = client.post(
        "/api/v1/commerce/marketplaces",
        json={
            "name": "API Marketplace",
            "slug": "api-marketplace",
        },
    )

    assert response.status_code == 201


def test_assign_and_get_product_brand():
    brand_res = client.post(
        "/api/v1/commerce/brands",
        json={
            "name": "Brand Lux",
            "slug": f"brand-lux-{uuid4()}",
        },
    )
    assert brand_res.status_code == 201
    brand_id = brand_res.json()["id"]

    product_id = str(uuid4())

    put_res = client.put(
        f"/api/v1/commerce/products/{product_id}/brand",
        json={"brand_id": brand_id},
    )
    assert put_res.status_code == 200
    assert put_res.json()["product_id"] == product_id
    assert put_res.json()["brand_id"] == brand_id

    get_res = client.get(f"/api/v1/commerce/products/{product_id}/brand")
    assert get_res.status_code == 200
    assert get_res.json()["brand_id"] == brand_id


def test_create_and_manage_listing():
    seller_res = client.post(
        "/api/v1/commerce/sellers",
        json={
            "name": "Listing Seller",
            "slug": f"seller-{uuid4()}",
            "seller_type": "brand",
        },
    )
    assert seller_res.status_code == 201
    seller_id = seller_res.json()["id"]

    mkt_res = client.post(
        "/api/v1/commerce/marketplaces",
        json={
            "name": "Listing Market",
            "slug": f"market-{uuid4()}",
        },
    )
    assert mkt_res.status_code == 201
    marketplace_id = mkt_res.json()["id"]

    product_id = str(uuid4())

    listing_res = client.post(
        "/api/v1/commerce/listings",
        json={
            "product_id": product_id,
            "seller_id": seller_id,
            "marketplace_id": marketplace_id,
            "external_reference": "EXT-12345",
        },
    )
    assert listing_res.status_code == 201
    listing_data = listing_res.json()
    listing_id = listing_data["id"]
    assert listing_data["status"] == "draft"

    status_res = client.post(
        f"/api/v1/commerce/listings/{listing_id}/status",
        json={"status": "active"},
    )
    assert status_res.status_code == 200
    assert status_res.json()["status"] == "active"

    get_res = client.get(f"/api/v1/commerce/listings/{listing_id}")
    assert get_res.status_code == 200
    assert get_res.json()["status"] == "active"

    prod_listings_res = client.get(f"/api/v1/commerce/products/{product_id}/listings")
    assert prod_listings_res.status_code == 200
    assert len(prod_listings_res.json()) >= 1

    seller_listings_res = client.get(f"/api/v1/commerce/sellers/{seller_id}/listings")
    assert seller_listings_res.status_code == 200
    assert len(seller_listings_res.json()) >= 1
