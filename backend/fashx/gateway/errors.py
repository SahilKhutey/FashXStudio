import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from schemas.common.errors import ErrorBody, ErrorResponse
from starlette import status

from fashx.core.errors import (
    ConsentRequiredError,
    DomainError,
    DuplicateEntityError,
    EntityNotFoundError,
    IdempotencyConflictError,
    ValidationError,
)

logger = logging.getLogger(__name__)


def install_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
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

    @app.exception_handler(EntityNotFoundError)
    async def entity_not_found_handler(request: Request, exc: EntityNotFoundError) -> JSONResponse:
        payload = ErrorResponse(
            error=ErrorBody(
                code=exc.code,
                message=exc.message,
                field=exc.field,
            )
        )
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content=payload.model_dump())

    @app.exception_handler(ConsentRequiredError)
    async def consent_required_handler(request: Request, exc: ConsentRequiredError) -> JSONResponse:
        payload = ErrorResponse(
            error=ErrorBody(
                code=exc.code,
                message=exc.message,
                field=exc.field,
            )
        )
        return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content=payload.model_dump())

    @app.exception_handler(DuplicateEntityError)
    async def duplicate_entity_handler(request: Request, exc: DuplicateEntityError) -> JSONResponse:
        payload = ErrorResponse(
            error=ErrorBody(
                code=exc.code,
                message=exc.message,
                field=exc.field,
            )
        )
        return JSONResponse(status_code=status.HTTP_409_CONFLICT, content=payload.model_dump())

    @app.exception_handler(IdempotencyConflictError)
    async def idempotency_conflict_handler(
        request: Request, exc: IdempotencyConflictError
    ) -> JSONResponse:
        payload = ErrorResponse(
            error=ErrorBody(
                code=exc.code,
                message=exc.message,
                field=exc.field,
            )
        )
        return JSONResponse(status_code=status.HTTP_409_CONFLICT, content=payload.model_dump())

    @app.exception_handler(ValidationError)
    async def domain_validation_handler(request: Request, exc: ValidationError) -> JSONResponse:
        payload = ErrorResponse(
            error=ErrorBody(
                code=exc.code,
                message=exc.message,
                field=exc.field,
            )
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, content=payload.model_dump()
        )

    @app.exception_handler(DomainError)
    async def generic_domain_handler(request: Request, exc: DomainError) -> JSONResponse:
        payload = ErrorResponse(
            error=ErrorBody(
                code=exc.code,
                message=exc.message,
                field=exc.field,
            )
        )
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=payload.model_dump())

    @app.exception_handler(Exception)
    async def unhandled_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled application error", exc_info=exc)
        payload = ErrorResponse(
            error=ErrorBody(code="internal_error", message="Internal server error.", field=None)
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=payload.model_dump()
        )
