"""SA-001, SA-006, SA-013, SA-014: Authorized HTTP Feed Adapter tests with mock transport."""

from __future__ import annotations

import httpx
import pytest

from fashx.catalog.acquisition.adapters.authorized_http_feed import (
    AuthorizedHttpFeedAdapter,
)
from fashx.catalog.acquisition.auth import ApiKeyAuthProvider
from fashx.catalog.acquisition.contracts_v2 import SourceHealthState
from fashx.catalog.acquisition.http_client import SourceHttpClient
from fashx.catalog.acquisition.registry import SourceConfig


@pytest.mark.asyncio
async def test_authorized_feed_json_fetch() -> None:
    """Test fetching and parsing a remote JSON product feed."""
    feed_payload = {
        "products": [
            {
                "source_product_id": "item-json-1",
                "title": "Chiffon Summer Top",
                "brand": "Aura",
                "price_minor": 149900,
                "currency": "INR",
                "category": "tops",
                "product_url": "https://partner.com/item/1",
                "image_url": "https://partner.com/images/1.jpg",
                "in_stock": True,
            }
        ],
        "next_cursor": None,
    }

    async def mock_handler(request: httpx.Request) -> httpx.Response:
        assert request.headers.get("X-API-Key") == "test-key"
        return httpx.Response(200, json=feed_payload, request=request)

    transport = httpx.MockTransport(mock_handler)
    http_client = SourceHttpClient(
        allowed_hostnames=["partner.com"],
        resolve_dns=False,
        transport=transport,
    )
    auth_provider = ApiKeyAuthProvider(api_key="test-key", header_name="X-API-Key")
    config = SourceConfig(source_slug="partner-feed", name="Partner Feed")

    adapter = AuthorizedHttpFeedAdapter(
        config=config,
        feed_url="https://partner.com/feed.json",
        auth_provider=auth_provider,
        http_client=http_client,
    )

    batch = await adapter.fetch_page()
    assert len(batch.products) == 1
    p = batch.products[0]
    assert p.source_product_id == "item-json-1"
    assert p.title == "Chiffon Summer Top"
    assert p.price_minor == 149900
    assert batch.has_more is False
    await adapter.close()


@pytest.mark.asyncio
async def test_authorized_feed_304_not_modified() -> None:
    """Test 304 Not Modified returns empty batch without errors."""

    async def mock_handler(request: httpx.Request) -> httpx.Response:
        assert request.headers.get("If-None-Match") == '"v123"'
        return httpx.Response(304, request=request)

    transport = httpx.MockTransport(mock_handler)
    http_client = SourceHttpClient(
        allowed_hostnames=["partner.com"],
        resolve_dns=False,
        transport=transport,
    )
    config = SourceConfig(source_slug="partner-feed", name="Partner Feed")

    adapter = AuthorizedHttpFeedAdapter(
        config=config,
        feed_url="https://partner.com/feed.json",
        http_client=http_client,
    )
    adapter._etag = '"v123"'

    batch = await adapter.fetch_page()
    assert len(batch.products) == 0
    assert batch.has_more is False
    await adapter.close()


@pytest.mark.asyncio
async def test_authorized_feed_health_check() -> None:
    """Test health check probe."""

    async def mock_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=b"OK", request=request)

    transport = httpx.MockTransport(mock_handler)
    http_client = SourceHttpClient(
        allowed_hostnames=["partner.com"],
        resolve_dns=False,
        transport=transport,
    )
    config = SourceConfig(source_slug="partner-feed", name="Partner Feed")

    adapter = AuthorizedHttpFeedAdapter(
        config=config,
        feed_url="https://partner.com/feed.json",
        http_client=http_client,
    )

    health = await adapter.health_check()
    assert health.state == SourceHealthState.HEALTHY
    await adapter.close()
