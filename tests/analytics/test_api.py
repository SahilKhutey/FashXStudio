from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from fashx.core.bootstrap import register_core_services
from fashx.core.runtime import get_core_runtime
from app.main import app

client = TestClient(app)


def test_analytics_routes_registered():
    paths = set(app.openapi()["paths"].keys())
    assert "/api/v1/analytics/events" in paths
    assert "/api/v1/analytics/aggregate" in paths


def test_record_event_api():
    runtime = get_core_runtime()
    register_core_services(runtime)
    app.state.core_runtime = runtime

    response = client.post(
        "/api/v1/analytics/events",
        json={
            "event_type": "product_viewed",
            "session_id": "session-1",
            "category": "footwear",
            "brand": "Nike",
            "region": "IN",
            "value": "4500.00",
            "properties": {
                "source": "home",
                "position": "3",
            },
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["event_type"] == "product_viewed"
    assert data["session_id"] == "session-1"
    assert data["region"] == "IN"
    assert data["category"] == "footwear"
    assert data["brand"] == "Nike"
    assert data["properties"]["source"] == "home"


def test_aggregate_events_api():
    runtime = get_core_runtime()
    register_core_services(runtime)
    app.state.core_runtime = runtime

    now = datetime.now(UTC)

    # Record two events via API
    client.post(
        "/api/v1/analytics/events",
        json={
            "event_type": "cart_line_added",
            "session_id": "s1",
            "region": "IN",
            "category": "apparel",
            "value": "1999.00",
            "occurred_at": now.isoformat(),
        },
    )
    client.post(
        "/api/v1/analytics/events",
        json={
            "event_type": "cart_line_added",
            "session_id": "s2",
            "region": "IN",
            "category": "apparel",
            "value": "2499.00",
            "occurred_at": (now + timedelta(minutes=5)).isoformat(),
        },
    )

    # Aggregate
    agg_response = client.post(
        "/api/v1/analytics/aggregate",
        json={
            "start": (now - timedelta(hours=1)).isoformat(),
            "end": (now + timedelta(hours=1)).isoformat(),
            "metric_name": "cart_additions",
            "period": "day",
        },
    )

    assert agg_response.status_code == 200
    data = agg_response.json()
    assert len(data) >= 1
    target_bucket = next(
        (b for b in data if b.get("dimensions", {}).get("category") == "apparel"),
        None,
    )
    assert target_bucket is not None
    assert target_bucket["count"] == 2
    assert target_bucket["metric_name"] == "cart_additions"
