import pytest
from fastapi import APIRouter, Depends, FastAPI
from fastapi.testclient import TestClient

from fashx.security.errors import ApiError, api_error_handler
from fashx.security.ratelimit import InMemoryRateLimiter, rate_limit


@pytest.mark.asyncio
async def test_in_memory_rate_limiter_window():
    limiter = InMemoryRateLimiter()
    key = "user-123"

    # Request 1 of 3
    r1 = await limiter.check(key, max_requests=3, window_seconds=10)
    assert r1.allowed is True
    assert r1.remaining == 2

    # Request 2 of 3
    r2 = await limiter.check(key, max_requests=3, window_seconds=10)
    assert r2.allowed is True
    assert r2.remaining == 1

    # Request 3 of 3
    r3 = await limiter.check(key, max_requests=3, window_seconds=10)
    assert r3.allowed is True
    assert r3.remaining == 0

    # Request 4 of 3 (rejected)
    r4 = await limiter.check(key, max_requests=3, window_seconds=10)
    assert r4.allowed is False
    assert r4.remaining == 0
    assert r4.reset_seconds > 0


def test_rate_limit_endpoint_headers_and_429():
    app = FastAPI()
    app.add_exception_handler(ApiError, api_error_handler)
    router = APIRouter()

    @router.get("/limited", dependencies=[Depends(rate_limit(max_requests=2, window_seconds=60, scope="test"))])
    async def limited():
        return {"status": "ok"}

    app.include_router(router)
    client = TestClient(app)

    # First request
    res1 = client.get("/limited")
    assert res1.status_code == 200
    assert res1.headers.get("X-RateLimit-Limit") == "2"
    assert res1.headers.get("X-RateLimit-Remaining") == "1"

    # Second request
    res2 = client.get("/limited")
    assert res2.status_code == 200
    assert res2.headers.get("X-RateLimit-Remaining") == "0"

    # Third request (exceeds limit)
    res3 = client.get("/limited")
    assert res3.status_code == 429
    assert res3.json()["title"] == "rate_limited"
    assert "Retry-After" in res3.headers
