from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def audit_api() -> dict[str, Any]:
    try:
        from fashx.main import app

        routes: list[dict[str, Any]] = []

        # Recursively collect routes from app and included routers
        def collect_routes(router_or_app: Any, current_prefix: str = "") -> None:
            for route in getattr(router_or_app, "routes", []):
                if hasattr(route, "routes"):
                    sub_prefix = current_prefix + getattr(route, "prefix", "")
                    collect_routes(route, sub_prefix)
                elif hasattr(route, "path"):
                    path = getattr(route, "path", "")
                    methods = sorted(getattr(route, "methods", set()) or set())
                    routes.append({
                        "path": path,
                        "methods": methods,
                        "name": getattr(route, "name", ""),
                        "tags": getattr(route, "tags", []),
                    })

        collect_routes(app)

        # Also pull from OpenAPI schema if routes list is minimal due to _IncludedRouter nesting
        try:
            openapi = app.openapi()
            paths = openapi.get("paths", {})
            openapi_routes = []
            for path, path_item in sorted(paths.items()):
                for method, op in path_item.items():
                    if method.upper() in {"GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"}:
                        openapi_routes.append({
                            "path": path,
                            "method": method.upper(),
                            "summary": op.get("summary", ""),
                            "tags": op.get("tags", []),
                        })
        except Exception as exc:
            openapi_routes = []
            logger.warning("Could not extract OpenAPI schema: %s", exc)

        return {
            "status": "success",
            "route_count": len(openapi_routes) if openapi_routes else len(routes),
            "openapi_endpoint_count": len(openapi.get("paths", {})) if "openapi" in locals() else len(routes),
            "routes": sorted(routes, key=lambda item: item["path"]),
            "endpoints": openapi_routes,
        }
    except Exception as exc:
        return {
            "status": "failed",
            "error": str(exc),
            "route_count": 0,
            "routes": [],
        }
