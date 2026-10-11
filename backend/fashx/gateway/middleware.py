import json
import logging
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from fashx.core.flags import MAINTENANCE_MODE, is_flag_enabled
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

        # Maintenance mode kill switch check (Rule 9.10)
        path = request.url.path
        exempt_prefixes = (
            "/api/v1/admin",
            "/healthz",
            "/api/v1/system/health",
            "/docs",
            "/openapi.json",
        )
        if not any(path.startswith(prefix) for prefix in exempt_prefixes):
            try:
                if await is_flag_enabled(MAINTENANCE_MODE, default=False):
                    return Response(
                        content=json.dumps({"detail": "System is undergoing maintenance. Please retry shortly."}),
                        status_code=503,
                        media_type="application/json",
                        headers={
                            "Retry-After": "60",
                            "X-Request-ID": request_id,
                            "X-Trace-ID": trace_id,
                        },
                    )
            except Exception:
                pass

        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Trace-ID"] = trace_id
            return response
        finally:
            clear_request_context()
