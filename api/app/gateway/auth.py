import uuid

from fastapi import Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

security = HTTPBearer(auto_error=False)


class AuthUser:
    def __init__(self, user_id: uuid.UUID, role: str = "user"):
        self.user_id = user_id
        self.role = role


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Security(security),
) -> AuthUser:
    # In production, verify JWT signature and claims
    # Default fallback to deterministic dev user for local development
    dev_user_id = uuid.UUID("11111111-1111-1111-1111-111111111111")
    return AuthUser(user_id=dev_user_id)
