from __future__ import annotations

from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from fashx.catalog.search.router import router as search_router
from fashx.core.database import get_db_session


@pytest.fixture
def search_client(search_sync_session: Session, setup_search_catalog: dict[str, Any]) -> TestClient:
    """Create test client with mocked DB session executing against seeded in-memory DB."""
    app = FastAPI()
    app.include_router(search_router, prefix="/api/v1")

    class MockAsyncSession:
        async def run_sync(self, fn: Any) -> Any:
            return fn(search_sync_session)

        async def commit(self) -> None:
            search_sync_session.commit()

        async def get(self, model: Any, ident: Any) -> Any:
            return search_sync_session.get(model, ident)

        def add(self, instance: Any) -> None:
            search_sync_session.add(instance)

    async def _override_get_db() -> Any:
        yield MockAsyncSession()

    app.dependency_overrides[get_db_session] = _override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def test_api_search_products_keyword(
    search_client: TestClient, setup_search_catalog: dict[str, Any]
) -> None:
    """Verify GET /api/v1/search/products with keyword query."""
    resp = search_client.get("/api/v1/search/products", params={"q": "shirt", "limit": 10})
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert data["total"] >= 1
    assert any("Shirt" in it["title"] for it in data["items"])


def test_api_search_products_filters(
    search_client: TestClient, setup_search_catalog: dict[str, Any]
) -> None:
    """Verify GET /api/v1/search/products with category and price filters."""
    cat = setup_search_catalog
    resp = search_client.get(
        "/api/v1/search/products",
        params={
            "category_id": str(cat["cat_tops"].id),
            "max_price": "1000",
            "in_stock": "true",
            "sort": "price_low",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    for it in data["items"]:
        assert float(it["price"]["amount"]) <= 1000.0


def test_api_semantic_search(
    search_client: TestClient, setup_search_catalog: dict[str, Any]
) -> None:
    """Verify POST /api/v1/search/semantic."""
    payload = {
        "query": "formal office shirt",
        "limit": 5,
        "filters": {"currency": "INR"},
    }
    resp = search_client.post("/api/v1/search/semantic", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert isinstance(data["total"], int)


def test_api_visual_search(
    search_client: TestClient, setup_search_catalog: dict[str, Any]
) -> None:
    """Verify POST /api/v1/search/visual."""
    cat = setup_search_catalog
    payload = {
        "query_image_asset_id": str(cat["asset1"].id),
        "limit": 5,
    }
    resp = search_client.post("/api/v1/search/visual", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "sort" in data


def test_api_search_suggestions(
    search_client: TestClient, setup_search_catalog: dict[str, Any]
) -> None:
    """Verify GET /api/v1/search/suggestions."""
    resp = search_client.get("/api/v1/search/suggestions", params={"q": "sh", "limit": 5})
    assert resp.status_code == 200
    data = resp.json()
    assert "suggestions" in data
    assert isinstance(data["suggestions"], list)


def test_api_search_facets(
    search_client: TestClient, setup_search_catalog: dict[str, Any]
) -> None:
    """Verify GET /api/v1/search/facets."""
    resp = search_client.get("/api/v1/search/facets", params={"q": "shirt"})
    assert resp.status_code == 200
    data = resp.json()
    assert "facets" in data
    assert "brands" in data["facets"]
    assert "categories" in data["facets"]


def test_api_search_events(
    search_client: TestClient, setup_search_catalog: dict[str, Any]
) -> None:
    """Verify POST /api/v1/search/events."""
    cat = setup_search_catalog
    payload = {
        "event_type": "product_click",
        "merchant_product_id": str(cat["mp1"].id),
        "rank_position": 1,
        "metadata_json": {"source": "integration_test"},
    }
    resp = search_client.post("/api/v1/search/events", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "recorded"
