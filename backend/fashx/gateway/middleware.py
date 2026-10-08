import logging
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from fashx.core.observability import clear_request_context, set_request_context

logger = logging.getLogger(__name__)


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable[[Request], object]) -> Response:
        request_id, trace_id = set_request_context(
            request.headers.get("X-Request-ID"),
            request.headers.get("X-Trace-ID"),
        )
        request.state.request_id = request_id
        request.state.trace_id = trace_id
        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Trace-ID"] = trace_id
            return response
        finally:
            clear_request_context()
