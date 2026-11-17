from __future__ import annotations

import json
import logging
import re
import time
from collections.abc import Callable
from uuid import uuid4

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from fashx.core.flags import MAINTENANCE_MODE, is_flag_enabled
from fashx.core.metrics import emit_metric
from fashx.core.observability import clear_request_context, set_request_context
from fashx.core.settings import get_settings
from fashx.core.tracing import extract_trace_id, generate_traceparent, is_valid_traceparent

logger = logging.getLogger(__name__)

# Strict validation regex for request IDs (prevents log injection or oversized header attacks)
REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]{1,64}$")


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable[[Request], object]) -> Response:
        settings = get_settings()
        env = getattr(settings, "env", "dev")

        # 1. Validate incoming X-Request-ID or generate new UUID4
        incoming_req_id = request.headers.get("X-Request-ID", "").strip()
        if incoming_req_id and REQUEST_ID_PATTERN.fullmatch(incoming_req_id):
            request_id = incoming_req_id
        else:
            request_id = str(uuid4())

        # 2. Extract or generate W3C trace context
        inbound_traceparent = request.headers.get("traceparent")
        if is_valid_traceparent(inbound_traceparent):
            traceparent = inbound_traceparent
            trace_id = extract_trace_id(inbound_traceparent)
        else:
            incoming_trace_id = request.headers.get("X-Trace-ID", "").strip()
            if incoming_trace_id and REQUEST_ID_PATTERN.fullmatch(incoming_trace_id):
                trace_id = incoming_trace_id
            else:
                trace_id = str(uuid4())
            traceparent = generate_traceparent()

        # 3. Establish execution context
        set_request_context(request_id, trace_id)
        request.state.request_id = request_id
        request.state.trace_id = trace_id
        request.state.traceparent = traceparent

        # 4. Maintenance mode kill switch check (Rule 9.10)
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
                    # Clean up context on maintenance mode path before returning early
                    clear_request_context()
                    return Response(
                        content=json.dumps({"detail": "System is undergoing maintenance. Please retry shortly."}),
                        status_code=503,
                        media_type="application/json",
                        headers={
                            "Retry-After": "60",
                            "X-Request-ID": request_id,
                            "X-Trace-ID": trace_id,
                            "traceparent": traceparent,
                        },
                    )
            except Exception:
                pass

        started = time.perf_counter()
        try:
            response = await call_next(request)  # type: ignore[assignment]
            duration_ms = round((time.perf_counter() - started) * 1000, 2)

            route = request.scope.get("route")
            route_template = getattr(route, "path", path)
            status_code = getattr(response, "status_code", 200)
            status_class = f"{status_code // 100}xx"

            response.headers["X-Request-ID"] = request_id
            response.headers["X-Trace-ID"] = trace_id
            response.headers["traceparent"] = traceparent

            logger.info(
                "http_request",
                extra={
                    "event": "http_request",
                    "request_id": request_id,
                    "trace_id": trace_id,
                    "method": request.method,
                    "route": route_template,
                    "status_code": status_code,
                    "duration_ms": duration_ms,
                    "service": "api",
                    "environment": env,
                },
            )

            # Emit CloudWatch Embedded Metric Format operational metrics
            dimensions = {
                "Route": route_template,
                "Method": request.method,
                "StatusClass": status_class,
            }
            emit_metric(
                "RequestLatency",
                duration_ms,
                unit="Milliseconds",
                service="api",
                environment=env,
                dimensions=dimensions,
                namespace="FashX/API",
            )
            emit_metric(
                "RequestCount",
                1.0,
                unit="Count",
                service="api",
                environment=env,
                dimensions=dimensions,
                namespace="FashX/API",
            )
            if status_code >= 500:
                emit_metric(
                    "Request5xxCount",
                    1.0,
                    unit="Count",
                    service="api",
                    environment=env,
                    dimensions={"Route": route_template, "Method": request.method},
                    namespace="FashX/API",
                )
            elif status_code >= 400:
                emit_metric(
                    "Request4xxCount",
                    1.0,
                    unit="Count",
                    service="api",
                    environment=env,
                    dimensions={"Route": route_template, "Method": request.method},
                    namespace="FashX/API",
                )

            return response
        except Exception:
            duration_ms = round((time.perf_counter() - started) * 1000, 2)
            route = request.scope.get("route")
            route_template = getattr(route, "path", path)

            logger.exception(
                "http_request_failed",
                extra={
                    "event": "http_request_failed",
                    "request_id": request_id,
                    "trace_id": trace_id,
                    "method": request.method,
                    "route": route_template,
                    "status_code": 500,
                    "duration_ms": duration_ms,
                    "service": "api",
                    "environment": env,
                },
            )

            emit_metric(
                "Request5xxCount",
                1.0,
                unit="Count",
                service="api",
                environment=env,
                dimensions={"Route": route_template, "Method": request.method},
                namespace="FashX/API",
            )
            raise
        finally:
            clear_request_context()
