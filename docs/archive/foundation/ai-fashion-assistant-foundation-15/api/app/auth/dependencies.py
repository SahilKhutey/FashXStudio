from __future__ import annotations

from uuid import UUID

from fastapi import Header, HTTPException, status

from api.app.core.settings import get_settings


async def current_user_id(x_user_id: str | None = Header(default=None, alias="X-User-ID")) -> UUID:
    """Development authentication bridge.

    The production contract is bearer-token based. Foundation 3 deliberately keeps
    the provider behind a dependency so Supabase/Auth0 can replace this bridge
    without changing feature routers or application services.
    """
    settings = get_settings()
    if not x_user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    try:
        return UUID(x_user_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user identity") from exc
