import time
from unittest.mock import MagicMock

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from fashx.security.deps import (
    Principal,
    get_principal,
    require_role,
    require_self,
)
from fashx.security.errors import ApiError
from fashx.security.identity import InMemoryIdentityRepo
from fashx.security.tokens import (
    Claims,
    JWKSVerifier,
    LocalJWTVerifier,
)
from tests.conftest import make_token

SECRET = "test-secret-key-at-least-32-chars-long"
ISSUER = "fashx-test"
AUDIENCE = "fashx-api"


def test_local_jwt_verifier_valid():
    verifier = LocalJWTVerifier(secret=SECRET, issuer=ISSUER, audience=AUDIENCE)
    token = make_token(sub="alice", iss=ISSUER, aud=AUDIENCE, secret=SECRET)
    claims = verifier.verify(token)
    assert isinstance(claims, Claims)
    assert claims.subject == "alice"
    assert claims.issuer == ISSUER


def test_local_jwt_verifier_expired():
    verifier = LocalJWTVerifier(secret=SECRET, issuer=ISSUER, audience=AUDIENCE)
    token = make_token(sub="alice", iss=ISSUER, aud=AUDIENCE, exp_delta_seconds=-100, secret=SECRET)
    with pytest.raises(ApiError) as exc_info:
        verifier.verify(token)
    assert exc_info.value.status == 401
    assert exc_info.value.code == "unauthorized"


def test_local_jwt_verifier_wrong_audience():
    verifier = LocalJWTVerifier(secret=SECRET, issuer=ISSUER, audience=AUDIENCE)
    token = make_token(sub="alice", iss=ISSUER, aud="wrong-audience", secret=SECRET)
    with pytest.raises(ApiError) as exc_info:
        verifier.verify(token)
    assert exc_info.value.status == 401


def test_local_jwt_verifier_wrong_issuer():
    verifier = LocalJWTVerifier(secret=SECRET, issuer=ISSUER, audience=AUDIENCE)
    token = make_token(sub="alice", iss="wrong-issuer", aud=AUDIENCE, secret=SECRET)
    with pytest.raises(ApiError) as exc_info:
        verifier.verify(token)
    assert exc_info.value.status == 401


def test_local_jwt_verifier_wrong_secret():
    verifier = LocalJWTVerifier(secret=SECRET, issuer=ISSUER, audience=AUDIENCE)
    token = make_token(sub="alice", iss=ISSUER, aud=AUDIENCE, secret="different-secret-key-32-chars-long")
    with pytest.raises(ApiError) as exc_info:
        verifier.verify(token)
    assert exc_info.value.status == 401


def test_local_jwt_verifier_missing_sub():
    verifier = LocalJWTVerifier(secret=SECRET, issuer=ISSUER, audience=AUDIENCE)
    now = int(time.time())
    payload = {"iss": ISSUER, "aud": AUDIENCE, "exp": now + 3600}
    token = jwt.encode(payload, SECRET, algorithm="HS256")
    with pytest.raises(ApiError) as exc_info:
        verifier.verify(token)
    assert exc_info.value.status == 401


def test_local_jwt_verifier_missing_exp():
    verifier = LocalJWTVerifier(secret=SECRET, issuer=ISSUER, audience=AUDIENCE)
    payload = {"sub": "alice", "iss": ISSUER, "aud": AUDIENCE}
    token = jwt.encode(payload, SECRET, algorithm="HS256")
    with pytest.raises(ApiError) as exc_info:
        verifier.verify(token)
    assert exc_info.value.status == 401


def test_local_jwt_verifier_algorithm_none_rejected():
    verifier = LocalJWTVerifier(secret=SECRET, issuer=ISSUER, audience=AUDIENCE)
    payload = {
        "sub": "alice",
        "iss": ISSUER,
        "aud": AUDIENCE,
        "exp": int(time.time()) + 3600,
    }
    # Unsecured JWT (alg="none")
    token = jwt.encode(payload, key="", algorithm="none")
    with pytest.raises(ApiError) as exc_info:
        verifier.verify(token)
    assert exc_info.value.status == 401


def test_jwks_verifier_rsa_mock():
    # Generate RSA key pair for testing
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    public_key = private_key.public_key()

    verifier = JWKSVerifier(
        jwks_url="https://auth.example.com/.well-known/jwks.json",
        issuer="https://auth.example.com",
        audience="fashx-api",
    )

    mock_signing_key = MagicMock()
    mock_signing_key.key = public_key
    verifier._client.get_signing_key_from_jwt = MagicMock(return_value=mock_signing_key)

    now = int(time.time())
    payload = {
        "sub": "bob",
        "iss": "https://auth.example.com",
        "aud": "fashx-api",
        "exp": now + 3600,
    }
    token = jwt.encode(payload, private_key, algorithm="RS256")

    claims = verifier.verify(token)
    assert claims.subject == "bob"
    assert claims.issuer == "https://auth.example.com"


def test_jwks_verifier_rejects_algorithm_confusion():
    # Attempt HS256 token against JWKSVerifier expecting RS256/ES256
    verifier = JWKSVerifier(
        jwks_url="https://auth.example.com/.well-known/jwks.json",
        issuer="https://auth.example.com",
        audience="fashx-api",
    )

    now = int(time.time())
    payload = {
        "sub": "attacker",
        "iss": "https://auth.example.com",
        "aud": "fashx-api",
        "exp": now + 3600,
    }
    token = jwt.encode(payload, "secret-key", algorithm="HS256")

    with pytest.raises(ApiError) as exc_info:
        verifier.verify(token)
    assert exc_info.value.status == 401


@pytest.mark.asyncio
async def test_in_memory_identity_repo():
    repo = InMemoryIdentityRepo()

    # Initial resolution creates identity
    identity1 = await repo.resolve(ISSUER, "user-1")
    assert identity1.role == "user"
    assert identity1.disabled is False
    assert identity1.user_id is not None

    # Deterministic resolution for same key
    identity2 = await repo.resolve(ISSUER, "user-1")
    assert identity1.user_id == identity2.user_id

    # Update role
    await repo.set_role(ISSUER, "user-1", "admin")
    identity_admin = await repo.resolve(ISSUER, "user-1")
    assert identity_admin.role == "admin"

    # Disable user
    await repo.disable(ISSUER, "user-1")
    identity_disabled = await repo.resolve(ISSUER, "user-1")
    assert identity_disabled.disabled is True


@pytest.mark.asyncio
async def test_get_principal_flow():
    verifier = LocalJWTVerifier(secret=SECRET, issuer=ISSUER, audience=AUDIENCE)
    repo = InMemoryIdentityRepo()

    # Valid request
    request = MagicMock()
    token = make_token(sub="alice", iss=ISSUER, aud=AUDIENCE, secret=SECRET)
    request.headers.get.return_value = f"Bearer {token}"

    principal = await get_principal(request, verifier=verifier, repo=repo)
    assert principal.subject == "alice"
    assert "user" in principal.roles
    assert not principal.is_admin

    # Missing header
    request_no_header = MagicMock()
    request_no_header.headers.get.return_value = None
    with pytest.raises(ApiError) as exc:
        await get_principal(request_no_header, verifier=verifier, repo=repo)
    assert exc.value.status == 401

    # Disabled account
    await repo.disable(ISSUER, "alice")
    with pytest.raises(ApiError) as exc:
        await get_principal(request, verifier=verifier, repo=repo)
    assert exc.value.status == 403


def test_require_role_and_self():
    p_user = Principal(user_id="user-123", subject="sub-123", roles=frozenset(["user"]))
    p_admin = Principal(user_id="admin-999", subject="sub-999", roles=frozenset(["admin"]))

    # require_role
    admin_checker = require_role("admin")
    assert admin_checker(p_admin) == p_admin
    with pytest.raises(ApiError) as exc:
        admin_checker(p_user)
    assert exc.value.status == 403

    # require_self
    assert require_self("user-123", p_user) == p_user
    with pytest.raises(ApiError) as exc:
        require_self("different-user", p_user)
    assert exc.value.status == 403
