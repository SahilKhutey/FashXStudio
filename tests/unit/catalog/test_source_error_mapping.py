"""SA-013: Granular error mapping across HTTP and protocol exceptions."""

from __future__ import annotations

import httpx

from fashx.catalog.acquisition.contracts_v2 import SourceErrorCode
from fashx.catalog.acquisition.errors import (
    AuthFailedError,
    CursorExpiredError,
    PermissionRevokedError,
    RateLimitedError,
    SchemaChangedError,
    map_provider_error,
)


def test_sa_013_http_status_mapping() -> None:
    req = httpx.Request("GET", "https://api.retailer.com")

    # 401 -> AUTHENTICATION
    err_401 = httpx.HTTPStatusError(
        "Unauthorized", request=req, response=httpx.Response(401, request=req)
    )
    assert map_provider_error(err_401) == SourceErrorCode.AUTHENTICATION

    # 403 -> AUTHORIZATION
    err_403 = httpx.HTTPStatusError(
        "Forbidden", request=req, response=httpx.Response(403, request=req)
    )
    assert map_provider_error(err_403) == SourceErrorCode.AUTHORIZATION

    # 404 -> NOT_FOUND
    err_404 = httpx.HTTPStatusError(
        "Not Found", request=req, response=httpx.Response(404, request=req)
    )
    assert map_provider_error(err_404) == SourceErrorCode.NOT_FOUND

    # 429 -> RATE_LIMITED
    err_429 = httpx.HTTPStatusError(
        "Rate Limit", request=req, response=httpx.Response(429, request=req)
    )
    assert map_provider_error(err_429) == SourceErrorCode.RATE_LIMITED

    # 500, 502, 503 -> TRANSIENT
    err_503 = httpx.HTTPStatusError(
        "Unavailable", request=req, response=httpx.Response(503, request=req)
    )
    assert map_provider_error(err_503) == SourceErrorCode.TRANSIENT


def test_sa_013_network_exception_mapping() -> None:
    req = httpx.Request("GET", "https://api.retailer.com")

    # Timeout -> TIMEOUT
    timeout_err = httpx.ReadTimeout("Timeout reached", request=req)
    assert map_provider_error(timeout_err) == SourceErrorCode.TIMEOUT

    # Network / Connection error -> TRANSIENT
    conn_err = httpx.ConnectError("Failed to connect", request=req)
    assert map_provider_error(conn_err) == SourceErrorCode.TRANSIENT


def test_sa_013_custom_error_mapping() -> None:
    assert map_provider_error(AuthFailedError("bad key")) == SourceErrorCode.AUTHENTICATION
    assert (
        map_provider_error(PermissionRevokedError("revoked")) == SourceErrorCode.PERMISSION_REVOKED
    )
    assert map_provider_error(RateLimitedError("rate")) == SourceErrorCode.RATE_LIMITED
    assert (
        map_provider_error(CursorExpiredError("expired cursor")) == SourceErrorCode.CURSOR_EXPIRED
    )
    assert (
        map_provider_error(SchemaChangedError("schema mismatch")) == SourceErrorCode.SCHEMA_CHANGED
    )
