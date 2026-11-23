"""SA-002, SA-003, SA-004, SA-005, SA-025: Source authentication interfaces and security."""

from __future__ import annotations

import base64

import pytest

from fashx.catalog.acquisition.auth import (
    ApiKeyAuthProvider,
    BasicAuthProvider,
    BearerTokenAuthProvider,
    NoAuthProvider,
    OAuth2ClientCredentialsProvider,
    SignedRequestAuthProvider,
)


@pytest.mark.asyncio
async def test_sa_002_no_auth_provider() -> None:
    provider = NoAuthProvider()
    material = await provider.get_auth_material("src1")
    assert material.headers == {}


@pytest.mark.asyncio
async def test_sa_002_api_key_auth_provider() -> None:
    provider = ApiKeyAuthProvider(api_key="secret-api-key-123", header_name="X-API-Key")
    material = await provider.get_auth_material("src1")
    assert material.headers["X-API-Key"] == "secret-api-key-123"

    # Missing API key fails closed
    with pytest.raises(ValueError) as exc_info:
        empty_provider = ApiKeyAuthProvider(api_key="")
        await empty_provider.get_auth_material("src1")
    assert "missing or empty" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_sa_002_bearer_token_provider() -> None:
    provider = BearerTokenAuthProvider(token="jwt-access-token-abc")
    material = await provider.get_auth_material("src1")
    assert material.headers["Authorization"] == "Bearer jwt-access-token-abc"

    # Missing token fails closed
    with pytest.raises(ValueError):
        empty_provider = BearerTokenAuthProvider(token="   ")
        await empty_provider.get_auth_material("src1")


@pytest.mark.asyncio
async def test_sa_002_basic_auth_provider() -> None:
    provider = BasicAuthProvider(username="merchant_user", password="secret_password")
    material = await provider.get_auth_material("src1")
    auth_header = material.headers["Authorization"]
    assert auth_header.startswith("Basic ")
    encoded = auth_header.split(" ")[1]
    decoded = base64.b64decode(encoded).decode("utf-8")
    assert decoded == "merchant_user:secret_password"


@pytest.mark.asyncio
async def test_sa_002_signed_request_provider() -> None:
    provider = SignedRequestAuthProvider(access_key="ACCESS_KEY", secret_key="SECRET_KEY")
    material = await provider.get_auth_material("src1")
    assert "X-FashX-Access-Key" in material.headers
    assert "X-FashX-Signature" in material.headers
    assert "X-FashX-Timestamp" in material.headers
    assert material.headers["X-FashX-Access-Key"] == "ACCESS_KEY"


@pytest.mark.asyncio
async def test_sa_003_oauth2_token_caching_and_refresh() -> None:
    """SA-003: OAuth2 client credentials caches token and refreshes when invalidated."""
    call_count = 0

    async def mock_resolver(client_id: str, client_secret: str) -> tuple[str, int]:
        nonlocal call_count
        call_count += 1
        return f"mock_token_{call_count}", 3600

    provider = OAuth2ClientCredentialsProvider(
        token_url="https://auth.retailer.com/oauth/token",
        client_id="client_id_val",
        client_secret="client_secret_val",
        mock_token_resolver=mock_resolver,
    )

    # First request fetches token
    mat1 = await provider.get_auth_material("src1")
    assert mat1.headers["Authorization"] == "Bearer mock_token_1"
    assert call_count == 1

    # Second request reuses cached token without calling resolver again
    mat2 = await provider.get_auth_material("src1")
    assert mat2.headers["Authorization"] == "Bearer mock_token_1"
    assert call_count == 1

    # Invalidate token and trigger refresh
    await provider.invalidate("src1")
    mat3 = await provider.get_auth_material("src1")
    assert mat3.headers["Authorization"] == "Bearer mock_token_2"
    assert call_count == 2


@pytest.mark.asyncio
async def test_sa_004_403_backoff_without_refresh() -> None:
    """SA-004: HTTP 403 Forbidden indicates permission revocation, blocking refresh loops."""
    provider = OAuth2ClientCredentialsProvider(
        token_url="https://auth.retailer.com/oauth/token",
        client_id="client_id_val",
        client_secret="client_secret_val",
    )
    provider.mark_forbidden()
    with pytest.raises(PermissionError) as exc_info:
        await provider.get_auth_material("src1")
    assert "FORBIDDEN" in str(exc_info.value)


def test_sa_005_sa_025_secret_redaction() -> None:
    """SA-005, SA-025: Secret credentials must not be exposed in repr or string conversions."""
    api_key_provider = ApiKeyAuthProvider(api_key="SUPER_SECRET_KEY_99999")
    assert "SUPER_SECRET_KEY_99999" not in repr(api_key_provider)
    assert "SUPER_SECRET_KEY_99999" not in str(api_key_provider)

    oauth_provider = OAuth2ClientCredentialsProvider(
        token_url="https://auth.example.com",
        client_id="client123",
        client_secret="SECRET_PASS_88888",
    )
    assert "SECRET_PASS_88888" not in repr(oauth_provider)
    assert "SECRET_PASS_88888" not in str(oauth_provider)
