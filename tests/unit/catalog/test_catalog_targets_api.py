"""Unit tests for Phase 05.7: Catalog Targets and Metrics Admin API Endpoints."""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from fashx.core.database import get_db_session
from fashx.main import app
from fashx.security.deps import Principal, get_principal


@pytest.fixture
def override_db(session_factory: async_sessionmaker[AsyncSession]):
    async def _get_test_session() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise

    prev = app.dependency_overrides.get(get_db_session)
    app.dependency_overrides[get_db_session] = _get_test_session
    yield
    if prev is not None:
        app.dependency_overrides[get_db_session] = prev
    else:
        app.dependency_overrides.pop(get_db_session, None)


@pytest.fixture
def test_client(override_db) -> TestClient:
    return TestClient(app)


def test_api_unauthorized_access_blocked(test_client: TestClient) -> None:
    """Non-admin / unauthenticated requests to admin catalog endpoints are rejected."""
    # Unauthenticated
    app.dependency_overrides.pop(get_principal, None)
    resp = test_client.get("/api/v1/admin/catalog/targets")
    assert resp.status_code in (401, 403)

    # Merchant role (not admin)
    app.dependency_overrides[get_principal] = lambda: Principal(
        user_id=str(uuid.uuid4()),
        subject="merchant-user",
        roles=frozenset(["merchant_operator"]),
    )
    resp2 = test_client.get("/api/v1/admin/catalog/targets")
    assert resp2.status_code == 403


def test_api_get_configured_targets(test_client: TestClient) -> None:
    """Admin can retrieve versioned targets configuration."""
    app.dependency_overrides[get_principal] = lambda: Principal(
        user_id=str(uuid.uuid4()),
        subject="admin-user",
        roles=frozenset(["admin"]),
    )

    resp = test_client.get("/api/v1/admin/catalog/targets")
    assert resp.status_code == 200
    body = resp.json()
    assert body["version"] == "1.0"
    assert body["pilot"]["minimum_live_authorized_sources"] == 1
    assert body["pilot"]["minimum_usable_offers"] == 1000
    assert body["quality"]["minimum_fresh_price_percentage"] == 95.0
    assert body["quality"]["maximum_broken_link_percentage_exclusive"] == 1.0
    assert body["quality"]["maximum_unauthorized_sources"] == 0
    assert body["quality"]["minimum_image_permission_traceability_percentage"] == 100.0


def test_api_run_and_retrieve_evaluation(test_client: TestClient) -> None:
    """Admin can trigger an evaluation run and retrieve its status and report."""
    admin_id = str(uuid.uuid4())
    app.dependency_overrides[get_principal] = lambda: Principal(
        user_id=admin_id,
        subject="admin-user",
        roles=frozenset(["admin"]),
    )

    # 1. Trigger evaluation
    post_resp = test_client.post("/api/v1/admin/catalog/evaluations?sample_size=10&random_seed=42")
    assert post_resp.status_code == 201
    post_body = post_resp.json()
    eval_id = post_body["evaluation_id"]
    assert post_body["status"] == "COMPLETED"
    assert "metric_results" in post_body
    assert "CAT-TGT-01" in post_body["metric_results"]
    assert "CAT-TGT-06" in post_body["metric_results"]

    # 2. Retrieve status
    get_resp = test_client.get(f"/api/v1/admin/catalog/evaluations/{eval_id}")
    assert get_resp.status_code == 200
    get_body = get_resp.json()
    assert get_body["evaluation_id"] == eval_id
    assert get_body["status"] == "COMPLETED"
    assert "metrics_summary" in get_body

    # 3. Retrieve full report
    report_resp = test_client.get(f"/api/v1/admin/catalog/evaluations/{eval_id}/report")
    assert report_resp.status_code == 200
    report_body = report_resp.json()
    assert report_body["evaluation_id"] == eval_id
    assert "detailed_report" in report_body


def test_api_get_specific_views(test_client: TestClient) -> None:
    """Admin can inspect individual quality, price freshness, and link health views."""
    app.dependency_overrides[get_principal] = lambda: Principal(
        user_id=str(uuid.uuid4()),
        subject="admin-user",
        roles=frozenset(["admin"]),
    )

    # Latest metrics
    resp_metrics = test_client.get("/api/v1/admin/catalog/metrics")
    assert resp_metrics.status_code == 200
    metrics_data = resp_metrics.json()
    assert "CAT-TGT-01" in metrics_data
    assert "CAT-TGT-02" in metrics_data

    # Source health
    resp_sh = test_client.get("/api/v1/admin/catalog/source-health")
    assert resp_sh.status_code == 200
    assert "live_sources_metric" in resp_sh.json()

    # Product quality
    resp_pq = test_client.get("/api/v1/admin/catalog/quality")
    assert resp_pq.status_code == 200
    assert "usable_offers_count" in resp_pq.json()

    # Price freshness
    resp_pf = test_client.get("/api/v1/admin/catalog/price-freshness?sample_size=10")
    assert resp_pf.status_code == 200
    assert "metric" in resp_pf.json()

    # Link health
    resp_lh = test_client.get("/api/v1/admin/catalog/link-health?sample_size=10")
    assert resp_lh.status_code == 200
    assert "metric" in resp_lh.json()

    # Image compliance
    resp_ic = test_client.get("/api/v1/admin/catalog/image-compliance")
    assert resp_ic.status_code == 200
    assert "metric" in resp_ic.json()
