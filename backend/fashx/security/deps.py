from collections.abc import Callable
from dataclasses import dataclass
from functools import lru_cache

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from fashx.core.database import get_db_session
from fashx.core.settings import get_settings

from .errors import forbidden, unauthorized
from .identity import IdentityRepo, SqlIdentityRepo
from .tokens import JWKSVerifier, LocalJWTVerifier, TokenVerifier


@dataclass(frozen=True)
class Principal:
    user_id: str
    subject: str
    roles: frozenset[str]

    @property
    def is_admin(self) -> bool:
        return "admin" in self.roles


@lru_cache(maxsize=1)
def get_verifier() -> TokenVerifier:
    settings = get_settings()
    if settings.auth_mode == "local":
        if not settings.auth_jwt_secret:
            raise ValueError("AUTH_JWT_SECRET required in local auth mode")
        return LocalJWTVerifier(
            secret=settings.auth_jwt_secret.get_secret_value(),
            issuer=settings.auth_issuer,
            audience=settings.auth_audience,
        )
    elif settings.auth_mode == "jwks":
        if not settings.auth_jwks_url:
            raise ValueError("AUTH_JWKS_URL required in jwks auth mode")
        return JWKSVerifier(
            jwks_url=settings.auth_jwks_url,
            issuer=settings.auth_issuer,
            audience=settings.auth_audience,
        )
    else:
        raise ValueError(f"Unsupported auth_mode: {settings.auth_mode}")


async def get_identity_repo(
    db: AsyncSession = Depends(get_db_session),
) -> IdentityRepo:
    return SqlIdentityRepo(db)


async def get_principal(
    request: Request,
    verifier: TokenVerifier = Depends(get_verifier),
    repo: IdentityRepo = Depends(get_identity_repo),
) -> Principal:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise unauthorized("Missing or invalid authorization header")

    token = auth_header[7:].strip()
    if not token:
        raise unauthorized("Token cannot be empty")

    claims = verifier.verify(token)
    identity = await repo.resolve(claims.issuer, claims.subject)
    if identity.disabled:
        raise forbidden("Account is disabled")

    return Principal(
        user_id=identity.user_id,
        subject=claims.subject,
        roles=frozenset([identity.role]),
    )


async def get_optional_principal(
    request: Request,
    verifier: TokenVerifier = Depends(get_verifier),
    repo: IdentityRepo = Depends(get_identity_repo),
) -> Principal | None:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None

    token = auth_header[7:].strip()
    if not token:
        return None

    try:
        claims = verifier.verify(token)
        identity = await repo.resolve(claims.issuer, claims.subject)
        if identity.disabled:
            return None
        return Principal(
            user_id=identity.user_id,
            subject=claims.subject,
            roles=frozenset([identity.role]),
        )
    except Exception:
        return None


def require_role(role: str) -> Callable[[Principal], Principal]:
    def _dependency(principal: Principal = Depends(get_principal)) -> Principal:
        if role not in principal.roles:
            raise forbidden(f"Role '{role}' required")
        return principal

    return _dependency


def require_self(
    user_id: str,
    principal: Principal = Depends(get_principal),
) -> Principal:
    if principal.user_id != user_id:
        raise forbidden("Forbidden: user_id mismatch")
    return principal
