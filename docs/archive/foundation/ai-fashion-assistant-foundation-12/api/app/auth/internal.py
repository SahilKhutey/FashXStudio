from __future__ import annotations

import secrets
from fastapi import Header

from api.app.core.errors import AuthorizationError
from api.app.core.settings import get_settings


async def require_internal_service(
    x_internal_service_token: str | None = Header(default=None, alias="X-Internal-Service-Token"),
) -> None:
    configured = get_settings().internal_service_token
    if not configured or not x_internal_service_token:
        raise AuthorizationError("Internal service authentication is not configured")
    if not secrets.compare_digest(x_internal_service_token, configured):
        raise AuthorizationError("Invalid internal service credentials")
