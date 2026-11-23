from __future__ import annotations

from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse


class CatalogAuthorizationError(Exception):
    """Base exception for catalog authorization domain."""

    def __init__(
        self,
        message_or_status: str | int = "",
        code: str = "catalog_authorization_error",
        message: str = "",
        details: Any = None,
        status_code: int = 400,
        **kwargs: Any,
    ) -> None:
        if isinstance(message_or_status, int):
            final_status = message_or_status
            final_msg = message or kwargs.get("message", "")
        else:
            final_status = kwargs.get("status_code", status_code)
            final_msg = message_or_status or message or kwargs.get("message", "")
        self.status_code = final_status
        self.code = code
        self.message = final_msg
        self.details = details
        super().__init__(final_msg)


class MerchantNotFoundError(CatalogAuthorizationError):
    def __init__(self, merchant_id: Any) -> None:
        super().__init__(
            status_code=404,
            code="merchant_not_found",
            message=f"Merchant '{merchant_id}' was not found.",
        )


class MerchantVerificationError(CatalogAuthorizationError):
    def __init__(self, message: str, code: str = "merchant_verification_failed") -> None:
        super().__init__(
            status_code=422,
            code=code,
            message=message,
        )


class SourceNotFoundError(CatalogAuthorizationError):
    def __init__(self, source_id: Any) -> None:
        super().__init__(
            status_code=404,
            code="source_not_found",
            message=f"Catalog source '{source_id}' was not found.",
        )


class SourceLifecycleError(CatalogAuthorizationError):
    def __init__(self, message: str, code: str = "source_lifecycle_invalid_transition") -> None:
        super().__init__(
            status_code=422,
            code=code,
            message=message,
        )


class PermissionDeniedError(CatalogAuthorizationError):
    def __init__(self, reason_code: str, message: str) -> None:
        self.reason_code = reason_code
        super().__init__(
            status_code=403,
            code=reason_code,
            message=message,
        )


class TakedownError(CatalogAuthorizationError):
    def __init__(self, message: str, code: str = "takedown_error") -> None:
        super().__init__(
            status_code=400,
            code=code,
            message=message,
        )


async def catalog_authorization_error_handler(
    request: Request, exc: CatalogAuthorizationError
) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "") or request.headers.get("x-request-id", "")
    content = {
        "error": {
            "code": exc.code,
            "message": exc.message,
            "details": exc.details,
            "request_id": request_id,
        }
    }
    return JSONResponse(status_code=exc.status_code, content=content)
