from fastapi import Request
from fastapi.responses import JSONResponse


class ApiError(Exception):
    def __init__(
        self,
        status: int,
        code: str,
        detail: str = "",
        headers: dict[str, str] | None = None,
    ) -> None:
        self.status = status
        self.code = code
        self.detail = detail
        self.headers = headers or {}


def unauthorized(detail: str = "Authentication required") -> ApiError:
    return ApiError(401, "unauthorized", detail, {"WWW-Authenticate": "Bearer"})


def forbidden(detail: str = "Not allowed") -> ApiError:
    return ApiError(403, "forbidden", detail)


def not_found(detail: str = "Not found") -> ApiError:
    return ApiError(404, "not_found", detail)


def too_many_requests(retry_after: int) -> ApiError:
    return ApiError(
        429,
        "rate_limited",
        "Too many requests",
        {"Retry-After": str(max(retry_after, 1))},
    )


async def api_error_handler(request: Request, exc: ApiError) -> JSONResponse:
    body = {
        "type": f"https://fashx.dev/errors/{exc.code}",
        "title": exc.code,
        "status": exc.status,
        "detail": exc.detail,
        "instance": request.url.path,
        "request_id": getattr(request.state, "request_id", None),
    }
    return JSONResponse(
        body,
        status_code=exc.status,
        headers=exc.headers,
        media_type="application/problem+json",
    )
