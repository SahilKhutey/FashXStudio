"""Amazon Cognito Access Token Verification Engine.

Performs offline cryptographic verification of Cognito access tokens using JWKS public keys.
Enforces:
1. RS256 signature verification via JWKS public key rotation.
2. Issuer validation against the configured Cognito User Pool.
3. App Client ID validation (Cognito access tokens use `client_id`, not `aud`).
4. Token use validation (`token_use == 'access'`, strictly rejecting ID tokens).
5. Token expiration with clock skew leeway.
6. Scope extraction and session tracking (`origin_jti` / `jti`).
"""

import logging
from dataclasses import dataclass
from typing import Any

import jwt
from jwt import PyJWKClient
from jwt.exceptions import (
    ExpiredSignatureError,
    ImmatureSignatureError,
    InvalidAlgorithmError,
    InvalidAudienceError,
    InvalidIssuerError,
    InvalidSignatureError,
    InvalidTokenError,
)

from fashx.core.settings import get_settings
from fashx.security.errors import unauthorized

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AuthenticatedIdentity:
    """Represents a verified shopper identity from an Amazon Cognito access token."""

    subject: str
    client_id: str
    scopes: frozenset[str]
    token_id: str | None
    session_id: str | None
    issuer: str
    claims: dict[str, Any]

    @property
    def user_id(self) -> str:
        """Alias for subject to conform with Principal resolution interfaces."""
        return self.subject


class CognitoTokenVerifier:
    """Verifies Amazon Cognito OAuth 2.0 access tokens against User Pool JWKS."""

    def __init__(
        self,
        jwks_url: str | None = None,
        issuer: str | None = None,
        client_id: str | None = None,
        jwks_client: PyJWKClient | None = None,
    ) -> None:
        settings = get_settings()
        self.issuer = issuer or settings.cognito_issuer or settings.auth_issuer
        self.client_id = client_id or settings.cognito_app_client_id or settings.auth_audience
        self.jwks_url = jwks_url or settings.cognito_jwks_url or settings.auth_jwks_url

        if not self.jwks_url:
            raise ValueError("Cognito JWKS URL is required for CognitoTokenVerifier")
        if not self.issuer:
            raise ValueError("Cognito issuer is required for CognitoTokenVerifier")
        if not self.client_id:
            raise ValueError("Cognito client_id is required for CognitoTokenVerifier")

        self._jwks_client = jwks_client or PyJWKClient(
            self.jwks_url,
            cache_keys=True,
            lifespan=3600,
            timeout=5,
        )

    def verify(self, token: str) -> AuthenticatedIdentity:
        """Verify token signature, claims, expiry, and app client binding."""
        if not token or not isinstance(token, str):
            raise unauthorized("Token cannot be empty")

        token_str = token.strip()
        if not token_str:
            raise unauthorized("Token cannot be empty")

        # 1. Retrieve signing key from JWKS
        try:
            signing_key = self._jwks_client.get_signing_key_from_jwt(token_str)
            key = signing_key.key
        except Exception as e:
            logger.warning("Failed to obtain signing key from JWKS for token: %s", type(e).__name__)
            raise unauthorized("Unable to verify token signature") from e

        # 2. Decode and verify signature, issuer, and expiration (RS256 only)
        try:
            claims = jwt.decode(
                token_str,
                key,
                algorithms=["RS256"],
                issuer=self.issuer,
                leeway=30,
                options={
                    "require": ["exp", "sub", "iss", "token_use"],
                    "verify_aud": False,  # Cognito access tokens use client_id, not aud
                },
            )
        except ExpiredSignatureError as e:
            raise unauthorized("Token has expired") from e
        except (
            InvalidSignatureError,
            InvalidAlgorithmError,
            InvalidIssuerError,
            InvalidAudienceError,
            ImmatureSignatureError,
            InvalidTokenError,
        ) as e:
            raise unauthorized("Invalid token") from e
        except Exception as e:
            raise unauthorized("Token verification failed") from e

        # 3. Verify token_use == 'access' (strictly reject ID tokens at API endpoints)
        token_use = claims.get("token_use")
        if token_use != "access":
            raise unauthorized(f"Invalid token_use: '{token_use}'. Access token required.")

        # 4. Verify client_id matches expected app client ID
        token_client_id = claims.get("client_id")
        if token_client_id != self.client_id:
            raise unauthorized("Token client_id does not match expected application client")

        # 5. Extract subject and scopes
        sub = str(claims.get("sub", "")).strip()
        if not sub:
            raise unauthorized("Token subject cannot be empty")

        raw_scope = claims.get("scope", "")
        scopes = (
            frozenset(s for s in raw_scope.split() if s)
            if isinstance(raw_scope, str)
            else frozenset()
        )

        token_id = claims.get("jti")
        # In Cognito, origin_jti represents the root session identifier across refreshes
        session_id = claims.get("origin_jti") or token_id

        return AuthenticatedIdentity(
            subject=sub,
            client_id=self.client_id,
            scopes=scopes,
            token_id=token_id,
            session_id=session_id,
            issuer=self.issuer,
            claims=claims,
        )
