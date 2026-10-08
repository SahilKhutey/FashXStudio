from decimal import Decimal
from uuid import uuid4

from fastapi.testclient import TestClient

from fashx.domain.recommendations.entities import RecommendationCandidate
from app.main import app
from fashx.repositories.recommendations.memory import (
    InMemoryRecommendationCandidateRepository,
)

client = TestClient(app)


def test_recommendation_route_exists():
    paths = set(app.openapi()["paths"].keys())
    assert "/api/v1/recommendations" in paths



def test_recommendation_api_post():
    from fashx.core.bootstrap import register_core_services
    from fashx.core.runtime import get_core_runtime

    runtime = get_core_runtime()
    register_core_services(runtime)
    app.state.core_runtime = runtime

    candidate_repo: InMemoryRecommendationCandidateRepository = (
        runtime.registry.get("recommendation_candidate_repository")
    )
    product_id = uuid4()

    candidate = RecommendationCandidate(
        product_id=product_id,
        title="Trendy Denim Jacket",
        category="jackets",
        style="vintage",
        brand="Levi's",
        price=Decimal("3499.00"),
        region="IN",
    )
    import asyncio
    asyncio.run(candidate_repo.add(candidate))

    response = client.post(
        "/api/v1/recommendations",
        json={
            "customer_id": str(uuid4()),
            "region": "IN",
            "category": "jackets",
            "style": "vintage",
            "limit": 5,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert data["total_candidates"] >= 1
    assert data["engine_version"] == "1.0"
    assert any(item["product_id"] == str(product_id) for item in data["items"])


def test_recommendation_api_validation_error():
    response = client.post(
        "/api/v1/recommendations",
        json={
            "min_price": 5000,
            "max_price": 1000,
        },
    )
    assert response.status_code == 422
