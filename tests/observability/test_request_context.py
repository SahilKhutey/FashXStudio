import asyncio
from unittest.mock import AsyncMock
from uuid import UUID

from fastapi import FastAPI
from fastapi.testclient import TestClient

from fashx.core.observability import get_request_id, get_trace_id
from fashx.gateway.middleware import RequestContextMiddleware
from fashx.tryon.ports_dispatch import CeleryTryOnJobDispatcher


def _create_test_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(RequestContextMiddleware)

    @app.get("/test-endpoint")
    async def test_endpoint():
        return {
            "req_id": get_request_id(),
            "trace_id": get_trace_id(),
        }

    @app.get("/error-endpoint")
    async def error_endpoint():
        raise RuntimeError("Deliberate test failure")

    return app


def test_request_without_id_generates_new_uuid():
    app = _create_test_app()
    client = TestClient(app)

    r = client.get("/test-endpoint")
    assert r.status_code == 200
    data = r.json()
    assert "X-Request-ID" in r.headers
    assert r.headers["X-Request-ID"] == data["req_id"]
    # Check valid UUID
    UUID(data["req_id"])
    assert get_request_id() == ""  # Context cleaned up


def test_valid_request_id_accepted():
    app = _create_test_app()
    client = TestClient(app)

    custom_id = "req-custom-alpha-123.456_789"
    r = client.get("/test-endpoint", headers={"X-Request-ID": custom_id})
    assert r.status_code == 200
    assert r.headers["X-Request-ID"] == custom_id
    assert r.json()["req_id"] == custom_id


def test_invalid_and_oversized_request_id_replaced():
    app = _create_test_app()
    client = TestClient(app)

    # 1. Invalid characters (spaces, semicolons, script tags)
    r_invalid = client.get("/test-endpoint", headers={"X-Request-ID": "<script>alert(1)</script>"})
    assert r_invalid.status_code == 200
    assert r_invalid.headers["X-Request-ID"] != "<script>alert(1)</script>"
    UUID(r_invalid.headers["X-Request-ID"])  # Generated valid UUID

    # 2. Excessively long ID (> 64 chars)
    oversized = "a" * 128
    r_long = client.get("/test-endpoint", headers={"X-Request-ID": oversized})
    assert r_long.status_code == 200
    assert r_long.headers["X-Request-ID"] != oversized
    UUID(r_long.headers["X-Request-ID"])


def test_failed_requests_clean_up_context():
    app = _create_test_app()
    client = TestClient(app, raise_server_exceptions=False)

    r = client.get("/error-endpoint")
    assert r.status_code == 500
    assert get_request_id() == ""
    assert get_trace_id() == ""


def test_maintenance_mode_cleans_up_context(monkeypatch):
    app = _create_test_app()
    client = TestClient(app)

    monkeypatch.setattr("fashx.gateway.middleware.is_flag_enabled", AsyncMock(return_value=True))
    r = client.get("/test-endpoint")
    assert r.status_code == 503
    assert "X-Request-ID" in r.headers
    assert get_request_id() == ""
    assert get_trace_id() == ""


def test_concurrent_requests_isolate_context():
    app = _create_test_app()
    client = TestClient(app)

    id1 = "req-isolation-1"
    id2 = "req-isolation-2"

    r1 = client.get("/test-endpoint", headers={"X-Request-ID": id1})
    r2 = client.get("/test-endpoint", headers={"X-Request-ID": id2})

    assert r1.json()["req_id"] == id1
    assert r2.json()["req_id"] == id2
    assert get_request_id() == ""


def test_celery_dispatch_propagates_correlation_headers(monkeypatch):
    captured_kwargs = {}

    class MockTask:
        def apply_async(self, *args, **kwargs):
            captured_kwargs.update(kwargs)

    monkeypatch.setattr("fashx.workers.app.process_tryon_job", MockTask())

    dispatcher = CeleryTryOnJobDispatcher()
    job_uuid = UUID("12345678-1234-5678-1234-567812345678")

    asyncio.run(dispatcher.dispatch(job_uuid))

    assert "headers" in captured_kwargs
    headers = captured_kwargs["headers"]
    assert "request_id" in headers
    assert "trace_id" in headers
    assert "traceparent" in headers
    assert headers["traceparent"].startswith("00-")
