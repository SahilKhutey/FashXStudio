from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_create_fashion_taxonomy():

    response = client.post(
        "/api/v1/fashion/taxonomy",
        json={
            "name": "Test Shirt",
            "slug": "test-shirt",
            "taxonomy_type": "garment",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "Test Shirt"
    assert data["slug"] == "test-shirt"


def test_get_fashion_taxonomy_and_children():
    res = client.post(
        "/api/v1/fashion/taxonomy",
        json={
            "name": "Footwear",
            "slug": "footwear",
            "taxonomy_type": "category",
        },
    )
    assert res.status_code == 201
    parent_id = res.json()["id"]

    child_res = client.post(
        "/api/v1/fashion/taxonomy",
        json={
            "name": "Sneakers",
            "slug": "sneakers",
            "taxonomy_type": "garment",
            "parent_id": parent_id,
        },
    )
    assert child_res.status_code == 201
    child_id = child_res.json()["id"]

    get_res = client.get(f"/api/v1/fashion/taxonomy/{child_id}")
    assert get_res.status_code == 200
    assert get_res.json()["slug"] == "sneakers"

    list_res = client.get(f"/api/v1/fashion/taxonomy?parent_id={parent_id}")
    assert list_res.status_code == 200
    assert any(item["id"] == child_id for item in list_res.json())


def test_classify_and_get_product_classification():
    tax_res = client.post(
        "/api/v1/fashion/taxonomy",
        json={
            "name": "Casual Style",
            "slug": "casual-style",
            "taxonomy_type": "style",
        },
    )
    assert tax_res.status_code == 201
    node_id = tax_res.json()["id"]

    product_id = str(uuid4())

    put_res = client.put(
        f"/api/v1/fashion/products/{product_id}/classification",
        json={
            "taxonomy_node_ids": [node_id],
            "attributes": [
                {"key": "color", "value": "black"},
                {"key": "fit", "value": "oversized"},
            ],
            "source": "manual",
            "confidence": 0.95,
        },
    )
    assert put_res.status_code == 200
    data = put_res.json()
    assert data["product_id"] == product_id
    assert node_id in data["taxonomy_node_ids"]
    assert data["confidence"] == 0.95

    get_res = client.get(f"/api/v1/fashion/products/{product_id}/classification")
    assert get_res.status_code == 200
    assert get_res.json()["product_id"] == product_id
