from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.errors import CoreError

STATUS_MAP: dict[str, int] = {
    "CORE_VALIDATION_ERROR": 422,
    "CORE_NOT_FOUND": 404,
    "CORE_CONFLICT": 409,
    "CORE_DEPENDENCY_ERROR": 503,
}


async def core_error_handler(
    request: Request,
    exc: CoreError,
) -> JSONResponse:
    status_code = STATUS_MAP.get(
        exc.code,
        500,
    )

    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            }
        },
    )
