from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

import jwt

from .errors import unauthorized

_REQUIRED = {"require": ["exp", "sub", "iss", "aud"]}


@dataclass(frozen=True)
class Claims:
    subject: str
    issuer: str


class TokenVerifier(Protocol):
    def verify(self, token: str) -> Claims: ...


class LocalJWTVerifier:
    """HS256 for dev/test only. Settings refuse this mode when ENV=prod."""

    def __init__(self, secret: str, issuer: str, audience: str) -> None:
        self._secret, self._iss, self._aud = secret, issuer, audience

    def verify(self, token: str) -> Claims:
        try:
            d = jwt.decode(
                token,
                self._secret,
                algorithms=["HS256"],
                audience=self._aud,
                issuer=self._iss,
                leeway=30,
                options=_REQUIRED,
            )
        except jwt.PyJWTError as e:
            raise unauthorized("Invalid token") from e
        return Claims(str(d["sub"]), str(d["iss"]))


class JWKSVerifier:
    def __init__(
        self,
        jwks_url: str,
        issuer: str,
        audience: str,
        algorithms: Sequence[str] = ("RS256", "ES256"),
    ) -> None:
        self._client = jwt.PyJWKClient(jwks_url, cache_keys=True, lifespan=3600)
        self._iss, self._aud, self._algs = issuer, audience, list(algorithms)

    def verify(self, token: str) -> Claims:
        try:
            key = self._client.get_signing_key_from_jwt(token).key
            d = jwt.decode(
                token,
                key,
                algorithms=self._algs,
                audience=self._aud,
                issuer=self._iss,
                leeway=30,
                options=_REQUIRED,
            )
        except jwt.PyJWTError as e:
            raise unauthorized("Invalid token") from e
        return Claims(str(d["sub"]), str(d["iss"]))


def create_demo_token(
    subject: str = "demo-evaluator-1",
    secret: str = "test-secret-key-at-least-32-chars-long",
    issuer: str = "fashx-test",
    audience: str = "fashx-api",
    exp_seconds: int = 86400 * 7,
) -> str:
    """Generate a signed HS256 JWT for invite-only/demo walkthroughs."""
    import time

    now = int(time.time())
    payload = {
        "sub": subject,
        "iss": issuer,
        "aud": audience,
        "exp": now + exp_seconds,
        "iat": now,
    }
    return jwt.encode(payload, secret, algorithm="HS256")
