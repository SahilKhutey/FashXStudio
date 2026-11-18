"""Provider error mapping and standard exceptions for catalog acquisition."""

from __future__ import annotations

import httpx

from fashx.catalog.acquisition.contracts_v2 import SourceErrorCode


class CatalogSourceError(Exception):
    """Base exception for catalog acquisition failures."""

    def __init__(self, message: str, error_code: SourceErrorCode) -> None:
        super().__init__(message)
        self.error_code = error_code


class AuthFailedError(CatalogSourceError):
    def __init__(self, message: str = "Provider authentication failed") -> None:
        super().__init__(message, SourceErrorCode.AUTHENTICATION)


class PermissionRevokedError(CatalogSourceError):
    def __init__(self, message: str = "Source permission revoked") -> None:
        super().__init__(message, SourceErrorCode.PERMISSION_REVOKED)


class RateLimitedError(CatalogSourceError):
    def __init__(
        self, message: str = "Provider rate limit exceeded", retry_after: float | None = None
    ) -> None:
        super().__init__(message, SourceErrorCode.RATE_LIMITED)
        self.retry_after = retry_after


class CursorExpiredError(CatalogSourceError):
    def __init__(self, message: str = "Pagination cursor has expired") -> None:
        super().__init__(message, SourceErrorCode.CURSOR_EXPIRED)


class SchemaChangedError(CatalogSourceError):
    def __init__(self, message: str = "Unexpected provider response structure") -> None:
        super().__init__(message, SourceErrorCode.SCHEMA_CHANGED)


def map_provider_error(exc: Exception) -> SourceErrorCode:
    """Map provider HTTP exceptions and network errors to stable SourceErrorCode."""
    if isinstance(exc, CatalogSourceError):
        return exc.error_code

    if isinstance(exc, httpx.HTTPStatusError):
        status = exc.response.status_code
        if status == 401:
            return SourceErrorCode.AUTHENTICATION
        if status == 403:
            return SourceErrorCode.AUTHORIZATION
        if status == 429:
            return SourceErrorCode.RATE_LIMITED
        if status == 404:
            return SourceErrorCode.NOT_FOUND
        if status in (500, 502, 503, 504):
            return SourceErrorCode.TRANSIENT
        if 400 <= status < 500:
            return SourceErrorCode.INVALID_REQUEST

    if isinstance(exc, (TimeoutError, httpx.TimeoutException)):
        return SourceErrorCode.TIMEOUT

    if isinstance(exc, (ConnectionError, httpx.NetworkError)):
        return SourceErrorCode.TRANSIENT

    return SourceErrorCode.TRANSIENT
