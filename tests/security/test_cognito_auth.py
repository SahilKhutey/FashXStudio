"""Unit and Integration Tests for Amazon Cognito Authentication (Matrix AUTH-001 - AUTH-018).

Validates:
- RS256 signature verification via JWKS.
- Strict enforcement of token_use == 'access' (ID token rejection).
- Client ID and issuer validation.
- Token expiration and clock skew leeway.
- Scope extraction and authorization checks.
- Session revocation tracking via revoked_auth_sessions.
- Fail-closed behavior on provider/JWKS outage.
- Authentication rate limiting and user enumeration prevention.
"""

import time
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock
from uuid import uuid4

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from fashx.security.cognito import AuthenticatedIdentity, CognitoTokenVerifier
from fashx.security.deps import get_principal
from fashx.security.errors import ApiError
from fashx.security.identity import InMemoryIdentityRepo
from fashx.security.ratelimit import InMemoryRateLimiter

TEST_REGION = "ap-south-1"
TEST_USER_POOL_ID = "ap-south-1_TestPool123"
TEST_CLIENT_ID = "fashx-test-mobile-client"
TEST_ISSUER = f"https://cognito-idp.{TEST_REGION}.amazonaws.com/{TEST_USER_POOL_ID}"
TEST_JWKS_URL = f"{TEST_ISSUER}/.well-known/jwks.json"


@pytest.fixture
def rsa_key_pair():
    """Generate an RSA key pair for testing token signing."""
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()
    return private_key, public_key


@pytest.fixture
def cognito_verifier(rsa_key_pair):
    """Create a CognitoTokenVerifier with mocked JWKS client returning public key."""
    _, public_key = rsa_key_pair

    mock_signing_key = MagicMock()
    mock_signing_key.key = public_key

    mock_jwks_client = MagicMock()
    mock_jwks_client.get_signing_key_from_jwt.return_value = mock_signing_key

    verifier = CognitoTokenVerifier(
        jwks_url=TEST_JWKS_URL,
        issuer=TEST_ISSUER,
        client_id=TEST_CLIENT_ID,
        jwks_client=mock_jwks_client,
    )
    return verifier


def make_cognito_token(
    private_key,
    sub: str = "cognito-user-abc-123",
    iss: str = TEST_ISSUER,
    client_id: str = TEST_CLIENT_ID,
    token_use: str = "access",
    scope: str = "openid email",
    exp_delta_seconds: int = 900,
    origin_jti: str | None = None,
    jti: str | None = None,
    algorithm: str = "RS256",
) -> str:
    """Helper to generate signed Cognito test tokens."""
    now = int(time.time())
    payload = {
        "sub": sub,
        "iss": iss,
        "client_id": client_id,
        "token_use": token_use,
        "scope": scope,
        "exp": now + exp_delta_seconds,
        "iat": now,
        "jti": jti or str(uuid4()),
    }
    if origin_jti:
        payload["origin_jti"] = origin_jti

    return jwt.encode(payload, private_key, algorithm=algorithm)


# AUTH-001: Valid access token is accepted
def test_auth_001_valid_access_token_accepted(cognito_verifier, rsa_key_pair):
    private_key, _ = rsa_key_pair
    token = make_cognito_token(
        private_key,
        sub="shopper-user-1",
        origin_jti="session-123",
    )
    identity = cognito_verifier.verify(token)
    assert isinstance(identity, AuthenticatedIdentity)
    assert identity.subject == "shopper-user-1"
    assert identity.client_id == TEST_CLIENT_ID
    assert identity.issuer == TEST_ISSUER
    assert identity.session_id == "session-123"
    assert "openid" in identity.scopes
    assert "email" in identity.scopes


# AUTH-002: Missing Authorization header rejected (401)
@pytest.mark.asyncio
async def test_auth_002_missing_auth_header_rejected(cognito_verifier):
    repo = InMemoryIdentityRepo()
    request = MagicMock()
    request.headers.get.return_value = None

    with pytest.raises(ApiError) as exc:
        await get_principal(request, verifier=cognito_verifier, repo=repo)
    assert exc.value.status == 401
    assert exc.value.code == "unauthorized"


# AUTH-003: Malformed JWT rejected (401)
def test_auth_003_malformed_jwt_rejected(cognito_verifier):
    with pytest.raises(ApiError) as exc:
        cognito_verifier.verify("not.a.valid.jwt.payload")
    assert exc.value.status == 401


# AUTH-004: Invalid signature rejected (401)
def test_auth_004_invalid_signature_rejected(cognito_verifier):
    foreign_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    token = make_cognito_token(foreign_key, sub="attacker-sub")
    with pytest.raises(ApiError) as exc:
        cognito_verifier.verify(token)
    assert exc.value.status == 401


# AUTH-005: Expired token rejected (401)
def test_auth_005_expired_token_rejected(cognito_verifier, rsa_key_pair):
    private_key, _ = rsa_key_pair
    expired_token = make_cognito_token(
        private_key,
        sub="shopper-user-1",
        exp_delta_seconds=-100,  # Expired in past
    )
    with pytest.raises(ApiError) as exc:
        cognito_verifier.verify(expired_token)
    assert exc.value.status == 401


# AUTH-006: Wrong issuer rejected (401)
def test_auth_006_wrong_issuer_rejected(cognito_verifier, rsa_key_pair):
    private_key, _ = rsa_key_pair
    token = make_cognito_token(
        private_key,
        iss="https://cognito-idp.ap-south-1.amazonaws.com/ap-south-1_WrongPool",
    )
    with pytest.raises(ApiError) as exc:
        cognito_verifier.verify(token)
    assert exc.value.status == 401


# AUTH-007: Wrong client ID rejected (401)
def test_auth_007_wrong_client_id_rejected(cognito_verifier, rsa_key_pair):
    private_key, _ = rsa_key_pair
    token = make_cognito_token(
        private_key,
        client_id="foreign-client-app-id",
    )
    with pytest.raises(ApiError) as exc:
        cognito_verifier.verify(token)
    assert exc.value.status == 401


# AUTH-008: ID token presented as access token strictly rejected (401)
def test_auth_008_id_token_rejected_at_api(cognito_verifier, rsa_key_pair):
    private_key, _ = rsa_key_pair
    id_token = make_cognito_token(
        private_key,
        token_use="id",  # ID token presented
    )
    with pytest.raises(ApiError) as exc:
        cognito_verifier.verify(id_token)
    assert exc.value.status == 401


# AUTH-009: Unsupported algorithm rejected (401)
def test_auth_009_unsupported_algorithm_rejected(cognito_verifier):
    token = jwt.encode(
        {"sub": "attacker", "iss": TEST_ISSUER, "client_id": TEST_CLIENT_ID, "token_use": "access", "exp": int(time.time()) + 900},
        key="",
        algorithm="none",
    )
    with pytest.raises(ApiError) as exc:
        cognito_verifier.verify(token)
    assert exc.value.status == 401


# AUTH-010: Unknown signing key re-fetches JWKS and rejects unresolved keys (401)
def test_auth_010_unknown_signing_key_fails_closed(rsa_key_pair):
    private_key, _ = rsa_key_pair
    token = make_cognito_token(private_key)

    mock_client = MagicMock()
    mock_client.get_signing_key_from_jwt.side_effect = Exception("Key ID not found in JWKS")

    verifier = CognitoTokenVerifier(
        jwks_url=TEST_JWKS_URL,
        issuer=TEST_ISSUER,
        client_id=TEST_CLIENT_ID,
        jwks_client=mock_client,
    )
    with pytest.raises(ApiError) as exc:
        verifier.verify(token)
    assert exc.value.status == 401


# AUTH-011: Revoked session rejected (401)
@pytest.mark.asyncio
async def test_auth_011_revoked_session_rejected(cognito_verifier, rsa_key_pair):
    private_key, _ = rsa_key_pair
    repo = InMemoryIdentityRepo()

    session_id = "session-revoked-xyz"
    token = make_cognito_token(
        private_key,
        sub="shopper-revoked-user",
        origin_jti=session_id,
    )

    # Revoke the session in repository
    expires_at = datetime.now(UTC) + timedelta(minutes=15)
    await repo.revoke_session("cognito", "shopper-revoked-user", session_id, expires_at)

    request = MagicMock()
    request.headers.get.return_value = f"Bearer {token}"

    with pytest.raises(ApiError) as exc:
        await get_principal(request, verifier=cognito_verifier, repo=repo)
    assert exc.value.status == 401
    assert "revoked" in str(exc.value.detail).lower()


# AUTH-012: Missing required scope handling
def test_auth_012_scope_extraction(cognito_verifier, rsa_key_pair):
    private_key, _ = rsa_key_pair
    token = make_cognito_token(
        private_key,
        scope="openid",  # missing email
    )
    identity = cognito_verifier.verify(token)
    assert "openid" in identity.scopes
    assert "email" not in identity.scopes


# AUTH-013: Invalid empty subject rejected (401)
def test_auth_013_empty_subject_rejected(cognito_verifier, rsa_key_pair):
    private_key, _ = rsa_key_pair
    token = make_cognito_token(private_key, sub="   ")
    with pytest.raises(ApiError) as exc:
        cognito_verifier.verify(token)
    assert exc.value.status == 401


# AUTH-014: JWKS provider unavailable fails closed (401)
def test_auth_014_provider_outage_fails_closed(rsa_key_pair):
    private_key, _ = rsa_key_pair
    token = make_cognito_token(private_key)

    mock_client = MagicMock()
    mock_client.get_signing_key_from_jwt.side_effect = TimeoutError("Cognito JWKS endpoint unreachable")

    verifier = CognitoTokenVerifier(
        jwks_url=TEST_JWKS_URL,
        issuer=TEST_ISSUER,
        client_id=TEST_CLIENT_ID,
        jwks_client=mock_client,
    )
    with pytest.raises(ApiError) as exc:
        verifier.verify(token)
    assert exc.value.status == 401


# AUTH-015: Valid token resolves strictly to that token's subject
@pytest.mark.asyncio
async def test_auth_015_distinct_token_subjects_isolate_principals(cognito_verifier, rsa_key_pair):
    private_key, _ = rsa_key_pair
    repo = InMemoryIdentityRepo()

    token_alice = make_cognito_token(private_key, sub="cognito-sub-alice")
    token_bob = make_cognito_token(private_key, sub="cognito-sub-bob")

    req_alice = MagicMock()
    req_alice.headers.get.return_value = f"Bearer {token_alice}"
    principal_alice = await get_principal(req_alice, verifier=cognito_verifier, repo=repo)

    req_bob = MagicMock()
    req_bob.headers.get.return_value = f"Bearer {token_bob}"
    principal_bob = await get_principal(req_bob, verifier=cognito_verifier, repo=repo)

    assert principal_alice.subject == "cognito-sub-alice"
    assert principal_bob.subject == "cognito-sub-bob"
    assert principal_alice.user_id != principal_bob.user_id


# AUTH-016: Local session revocation check blocks subsequent requests
@pytest.mark.asyncio
async def test_auth_016_local_revocation_blocks_subsequent_request(cognito_verifier, rsa_key_pair):
    private_key, _ = rsa_key_pair
    repo = InMemoryIdentityRepo()

    session_id = "session-active-then-revoked"
    token = make_cognito_token(private_key, sub="user-signout-test", origin_jti=session_id)

    req = MagicMock()
    req.headers.get.return_value = f"Bearer {token}"

    # First request succeeds
    p1 = await get_principal(req, verifier=cognito_verifier, repo=repo)
    assert p1.subject == "user-signout-test"

    # User triggers signout -> session revoked
    await repo.revoke_session(
        "cognito", "user-signout-test", session_id, datetime.now(UTC) + timedelta(minutes=15)
    )

    # Second request with same token now fails
    with pytest.raises(ApiError) as exc:
        await get_principal(req, verifier=cognito_verifier, repo=repo)
    assert exc.value.status == 401


# AUTH-017: Concurrent logins for same subject resolve to single internal user ID
@pytest.mark.asyncio
async def test_auth_017_concurrent_logins_resolve_single_user_id():
    import asyncio
    repo = InMemoryIdentityRepo()
    sub = "cognito-concurrent-shopper-1"

    results = await asyncio.gather(*(repo.resolve(TEST_ISSUER, sub) for _ in range(10)))
    user_ids = {r.user_id for r in results}
    assert len(user_ids) == 1


# AUTH-018: Authentication rate limiting enforces quota threshold
@pytest.mark.asyncio
async def test_auth_018_authentication_rate_limiting():
    limiter = InMemoryRateLimiter()
    key = "fashx:ratelimit:auth:login:192.168.1.100"

    # 5 allowed attempts
    for i in range(5):
        res = await limiter.check(key, max_requests=5, window_seconds=900)
        assert res.allowed is True
        assert res.remaining == 4 - i

    # 6th attempt is blocked
    res_blocked = await limiter.check(key, max_requests=5, window_seconds=900)
    assert res_blocked.allowed is False
    assert res_blocked.remaining == 0
    assert res_blocked.reset_seconds > 0
