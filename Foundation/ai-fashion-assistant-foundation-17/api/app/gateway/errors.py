import logging
from collections.abc import Callable

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette import status

from schemas.common.errors import ErrorBody, ErrorResponse
from api.app.core.errors import AppError

logger = logging.getLogger(__name__)


def install_exception_handlers(app) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        payload = ErrorResponse(
            error=ErrorBody(code=exc.code, message=exc.message, field=exc.field)
        )
        return JSONResponse(status_code=exc.status_code, content=payload.model_dump())

    @app.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, exc: RequestValidationError):
        field = None
        if exc.errors():
            loc = exc.errors()[0].get("loc", ())
            if loc:
                field = ".".join(str(p) for p in loc if p not in {"body", "query", "path"}) or None
        payload = ErrorResponse(
            error=ErrorBody(
                code="validation_error",
                message="Request validation failed.",
                field=field,
            )
        )
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=payload.model_dump())

    @app.exception_handler(Exception)
    async def unhandled_handler(request: Request, exc: Exception):
        logger.exception("Unhandled application error", exc_info=exc)
        payload = ErrorResponse(
            error=ErrorBody(code="internal_error", message="Internal server error.", field=None)
        )
        return JSONResponse(status_code=500, content=payload.model_dump())
