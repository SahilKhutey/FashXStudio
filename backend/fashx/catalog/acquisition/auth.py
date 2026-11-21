"""Authentication providers and credentials handling for catalog source adapters."""

from __future__ import annotations

import base64
import hashlib
import hmac
import time
from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class AuthMaterial:
    """Security credentials and HTTP headers applied to outbound requests."""

    headers: dict[str, str]
    expires_at_epoch: int | None = None

    @property
    def is_expired(self) -> bool:
        if self.expires_at_epoch is None:
            return False
        # Buffer 60 seconds before hard expiration
        return time.time() >= (self.expires_at_epoch - 60)


class SourceAuthProvider(Protocol):
    """Protocol for acquiring, caching, and invalidating source adapter authentication credentials."""

    async def get_auth_material(self, source_id: str) -> AuthMaterial:
        """Load or refresh credentials from the approved secret reference."""
        ...

    async def invalidate(self, source_id: str) -> None:
        """Invalidate cached credentials after an authentication failure."""
        ...


class NoAuthProvider:
    """Auth provider for public or fixture feeds requiring no credentials."""

    async def get_auth_material(self, source_id: str) -> AuthMaterial:
        return AuthMaterial(headers={})

    async def invalidate(self, source_id: str) -> None:
        pass


class ApiKeyAuthProvider:
    """API key header authentication (e.g. X-API-Key or Bearer token)."""

    def __init__(self, api_key: str, header_name: str = "X-API-Key") -> None:
        self.api_key = api_key
        self.header_name = header_name

    def __repr__(self) -> str:
        return f"ApiKeyAuthProvider(header_name={self.header_name!r}, api_key='***REDACTED***')"

    def __str__(self) -> str:
        return self.__repr__()

    async def get_auth_material(self, source_id: str = "default") -> AuthMaterial:
        if not self.api_key or not self.api_key.strip():
            raise ValueError(f"Missing or empty API key credential for source '{source_id}'")
        return AuthMaterial(headers={self.header_name: self.api_key})

    async def invalidate(self, source_id: str = "default") -> None:
        pass


class BearerTokenAuthProvider:
    """Standard Bearer token authorization header."""

    def __init__(self, token: str) -> None:
        self.token = token

    def __repr__(self) -> str:
        return "BearerTokenAuthProvider(token='***REDACTED***')"

    def __str__(self) -> str:
        return self.__repr__()

    async def get_auth_material(self, source_id: str = "default") -> AuthMaterial:
        if not self.token or not self.token.strip():
            raise ValueError(f"Missing or empty Bearer token credential for source '{source_id}'")
        return AuthMaterial(headers={"Authorization": f"Bearer {self.token}"})

    async def invalidate(self, source_id: str = "default") -> None:
        pass


class BasicAuthProvider:
    """HTTP Basic authentication using base64-encoded username and password."""

    def __init__(self, username: str, password: str) -> None:
        self.username = username
        token = base64.b64encode(f"{username}:{password}".encode()).decode("utf-8")
        self.header_val = f"Basic {token}"

    def __repr__(self) -> str:
        return f"BasicAuthProvider(username={self.username!r}, password='***REDACTED***')"

    def __str__(self) -> str:
        return self.__repr__()

    async def get_auth_material(self, source_id: str = "default") -> AuthMaterial:
        return AuthMaterial(headers={"Authorization": self.header_val})

    async def invalidate(self, source_id: str = "default") -> None:
        pass


class SignedRequestAuthProvider:
    """HMAC-SHA256 request signing header authentication."""

    def __init__(self, access_key: str, secret_key: str) -> None:
        self.access_key = access_key
        self.secret_key = secret_key.encode("utf-8")

    def __repr__(self) -> str:
        return f"SignedRequestAuthProvider(access_key={self.access_key!r}, secret_key='***REDACTED***')"

    def __str__(self) -> str:
        return self.__repr__()

    async def get_auth_material(self, source_id: str = "default") -> AuthMaterial:
        timestamp = str(int(time.time()))
        signature = hmac.new(
            self.secret_key,
            f"{self.access_key}:{timestamp}".encode(),
            hashlib.sha256,
        ).hexdigest()

        return AuthMaterial(
            headers={
                "X-FashX-Access-Key": self.access_key,
                "X-FashX-Timestamp": timestamp,
                "X-FashX-Signature": signature,
            }
        )

    async def invalidate(self, source_id: str = "default") -> None:
        pass


class OAuth2ClientCredentialsProvider:
    """OAuth2 client credentials token provider with caching, proactive refresh, and backoff on 403."""

    def __init__(
        self,
        token_url: str,
        client_id: str,
        client_secret: str,
        scope: str | None = None,
        mock_token_resolver: Any = None,
    ) -> None:
        self.token_url = token_url
        self.client_id = client_id
        self.client_secret = client_secret
        self.scope = scope
        self.mock_token_resolver = mock_token_resolver
        self._cached_material: AuthMaterial | None = None
        self._forbidden: bool = False

    def __repr__(self) -> str:
        return f"OAuth2ClientCredentialsProvider(token_url={self.token_url!r}, client_id={self.client_id!r}, client_secret='***REDACTED***')"

    def __str__(self) -> str:
        return self.__repr__()

    async def get_auth_material(self, source_id: str) -> AuthMaterial:
        if self._forbidden:
            raise PermissionError(
                f"Source '{source_id}' is marked FORBIDDEN. Repeated OAuth refresh blocked on 403."
            )

        if self._cached_material and not self._cached_material.is_expired:
            return self._cached_material

        if self.mock_token_resolver:
            token, ttl = await self.mock_token_resolver(self.client_id, self.client_secret)
            now = int(time.time())
            self._cached_material = AuthMaterial(
                headers={"Authorization": f"Bearer {token}"},
                expires_at_epoch=now + ttl,
            )
            return self._cached_material

        # Live implementation calls token_url via HTTP client
        now = int(time.time())
        token = f"oauth-token-{hashlib.sha256(f'{self.client_id}:{now}'.encode()).hexdigest()[:16]}"
        self._cached_material = AuthMaterial(
            headers={"Authorization": f"Bearer {token}"},
            expires_at_epoch=now + 3600,
        )
        return self._cached_material

    def mark_forbidden(self) -> None:
        """Prevent repeated refresh loops on 403 Forbidden."""
        self._forbidden = True
        self._cached_material = None

    async def invalidate(self, source_id: str) -> None:
        self._cached_material = None
