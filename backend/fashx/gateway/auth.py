from __future__ import annotations

import secrets
from typing import Optional
from uuid import UUID

from fastapi import Header, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from fashx.core.errors import AuthorizationError
from fashx.core.settings import get_settings

security = HTTPBearer(auto_error=False)


class AuthUser:
    def __init__(self, user_id: UUID, role: str = "user"):
        self.user_id = user_id
        self.role = role


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security),
) -> AuthUser:
    # In production, verify JWT signature and claims
    # Default fallback to deterministic dev user for local development
    dev_user_id = UUID("11111111-1111-1111-1111-111111111111")
    return AuthUser(user_id=dev_user_id)


async def current_user_id(x_user_id: str | None = Header(default=None, alias="X-User-ID")) -> UUID:
    if not x_user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    try:
        return UUID(x_user_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user identity") from exc


async def require_internal_service(
    x_internal_service_token: str | None = Header(default=None, alias="X-Internal-Service-Token"),
) -> None:
    configured = get_settings().internal_service_token
    if not configured or not x_internal_service_token:
        raise AuthorizationError("Internal service authentication is not configured")
    if not secrets.compare_digest(x_internal_service_token, configured):
        raise AuthorizationError("Invalid internal service credentials")

