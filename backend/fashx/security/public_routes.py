"""Public route definitions and allowlist."""

PUBLIC_EXACT_ROUTES: frozenset[str] = frozenset({
    "/",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/api/v1/system/health/live",
    "/api/v1/system/health/ready",
    "/api/v1/system/health",
    "/api/v1/system/ready",
})

PUBLIC_PREFIXES: tuple[str, ...] = (
    "/docs",
    "/redoc",
    "/openapi.json",
)


def is_public_path(path: str) -> bool:
    """Check if the given request path is an explicitly allowlisted public route."""
    if path in PUBLIC_EXACT_ROUTES:
        return True
    return any(path.startswith(prefix) for prefix in PUBLIC_PREFIXES)
