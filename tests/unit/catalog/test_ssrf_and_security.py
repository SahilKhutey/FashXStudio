"""SA-020, SA-021, SA-022, SA-023, SA-025: Network security, SSRF protection, size limits."""

from __future__ import annotations

import httpx
import pytest

from fashx.catalog.acquisition.http_client import (
    ResponseSizeExceededError,
    SecurityViolationError,
    SourceHttpClient,
    validate_source_url,
)


def test_sa_021_host_allowlist_enforcement() -> None:
    """SA-021: Requests to domains not in the explicit allowlist are rejected."""
    allowed = ["api.partner.com", "cdn.partner.com"]

    # Allowed host passes (resolve_dns=False for test mock)
    validated = validate_source_url(
        "https://api.partner.com/v1/products",
        allowed_hostnames=allowed,
        resolve_dns=False,
    )
    assert "https://api.partner.com" in validated

    # Unauthorized host fails
    with pytest.raises(SecurityViolationError) as exc:
        validate_source_url(
            "https://evil-host.com/products",
            allowed_hostnames=allowed,
            resolve_dns=False,
        )
    assert "not in the approved source host allowlist" in str(exc.value)


def test_sa_022_ssrf_loopback_and_private_network_blocking() -> None:
    """SA-022: Loopback, private subnets, link-local metadata services are strictly blocked."""
    disallowed_urls = [
        "https://127.0.0.1/admin",
        "https://10.0.0.5/api",
        "https://172.16.0.10/api",
        "https://192.168.1.1/api",
        "https://169.254.169.254/latest/meta-data/",  # Cloud metadata
        "https://0.0.0.0/",
    ]
    for url in disallowed_urls:
        with pytest.raises(SecurityViolationError) as exc:
            validate_source_url(url, require_https=False, resolve_dns=True)
        assert "SSRF violation" in str(exc.value)


def test_sa_022_disallow_non_http_schemes() -> None:
    """SA-022: File, FTP, Gopher, and custom schemes are strictly rejected."""
    with pytest.raises(SecurityViolationError) as exc1:
        validate_source_url("file:///etc/passwd", require_https=False, resolve_dns=False)
    assert "Unsupported scheme" in str(exc1.value)

    with pytest.raises(SecurityViolationError) as exc2:
        validate_source_url("gopher://127.0.0.1:70", require_https=False, resolve_dns=False)
    assert "Unsupported scheme" in str(exc2.value)

    with pytest.raises(SecurityViolationError) as exc3:
        validate_source_url("ftp://server/resource", require_https=False, resolve_dns=False)
    assert "Unsupported scheme" in str(exc3.value)


@pytest.mark.asyncio
async def test_sa_023_response_size_limit_enforcement() -> None:
    """SA-023: Responses exceeding maximum allowed size (e.g. 10MB) are aborted."""

    # Test via mock transport that returns headers with large content-length
    async def mock_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            headers={"content-length": "20971520"},  # 20MB
            content=b"test",
            request=request,
        )

    transport = httpx.MockTransport(mock_handler)
    client = SourceHttpClient(
        max_response_bytes=10 * 1024 * 1024,
        resolve_dns=False,
        transport=transport,
    )

    with pytest.raises(ResponseSizeExceededError) as exc:
        await client.get_response("https://api.example.com/huge-feed.json")
    assert "exceeds limit" in str(exc.value)
    await client.close()
