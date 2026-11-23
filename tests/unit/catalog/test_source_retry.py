"""SA-011, SA-012: Bounded retry policy and non-retryable error handling."""

from __future__ import annotations

from unittest.mock import AsyncMock

import httpx
import pytest

from fashx.catalog.acquisition.auth import ApiKeyAuthProvider
from fashx.catalog.acquisition.retry import SourceRetryPolicy


@pytest.mark.asyncio
async def test_sa_011_bounded_retry_on_server_errors() -> None:
    """SA-011: Server errors (500, 502, 503, 504) are retried up to max_attempts."""
    policy = SourceRetryPolicy(max_attempts=3, initial_delay_seconds=0.01, multiplier=1.5)

    call_count = 0

    async def flaky_call():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            req = httpx.Request("GET", "https://api.example.com")
            resp = httpx.Response(503, request=req)
            raise httpx.HTTPStatusError("Service Unavailable", request=req, response=resp)
        return "success"

    result = await policy.execute(flaky_call)
    assert result == "success"
    assert call_count == 3


@pytest.mark.asyncio
async def test_sa_011_exhausted_retries_raises() -> None:
    """SA-011: Once max_attempts is reached, error is raised."""
    policy = SourceRetryPolicy(max_attempts=3, initial_delay_seconds=0.01)

    call_count = 0

    async def failing_call():
        nonlocal call_count
        call_count += 1
        req = httpx.Request("GET", "https://api.example.com")
        resp = httpx.Response(500, request=req)
        raise httpx.HTTPStatusError("Internal Server Error", request=req, response=resp)

    with pytest.raises(httpx.HTTPStatusError):
        await policy.execute(failing_call)
    assert call_count == 3


@pytest.mark.asyncio
async def test_sa_012_non_retryable_errors_fail_fast() -> None:
    """SA-012: 400 Bad Request and 404 Not Found fail immediately without retry."""
    policy = SourceRetryPolicy(max_attempts=3, initial_delay_seconds=0.01)

    call_count = 0

    async def client_error_call():
        nonlocal call_count
        call_count += 1
        req = httpx.Request("GET", "https://api.example.com")
        resp = httpx.Response(404, request=req)
        raise httpx.HTTPStatusError("Not Found", request=req, response=resp)

    with pytest.raises(httpx.HTTPStatusError):
        await policy.execute(client_error_call)
    assert call_count == 1  # No retries on 404


@pytest.mark.asyncio
async def test_sa_012_401_single_refresh_retry() -> None:
    """SA-012: 401 triggers single token refresh callback then re-attempts once."""
    policy = SourceRetryPolicy(max_attempts=3, initial_delay_seconds=0.01)

    auth_provider = ApiKeyAuthProvider(api_key="valid-key")
    auth_provider.invalidate = AsyncMock()  # type: ignore[method-assign]

    call_count = 0

    async def auth_error_then_ok():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            req = httpx.Request("GET", "https://api.example.com")
            resp = httpx.Response(401, request=req)
            raise httpx.HTTPStatusError("Unauthorized", request=req, response=resp)
        return "authenticated_data"

    res = await policy.execute(auth_error_then_ok, source_id="src1", auth_provider=auth_provider)
    assert res == "authenticated_data"
    assert call_count == 2
    auth_provider.invalidate.assert_awaited_once_with("src1")
