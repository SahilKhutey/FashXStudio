"""Unit tests for source adapters and circuit breaker mechanics."""

import time

import pytest

from fashx.catalog.acquisition.adapters.amazon import AmazonAdapter
from fashx.catalog.acquisition.adapters.base import BaseSourceAdapter, CircuitBreakerOpenError
from fashx.catalog.acquisition.adapters.flipkart import FlipkartAdapter
from fashx.catalog.acquisition.adapters.myntra import MyntraAdapter
from fashx.catalog.acquisition.adapters.partner_feed import PartnerFeedAdapter
from fashx.catalog.acquisition.contract import AcquisitionBatch, SourceProduct
from fashx.catalog.acquisition.registry import SourceConfig


@pytest.mark.asyncio
async def test_partner_feed_pagination() -> None:
    items = [
        SourceProduct(
            source_slug="partner-feed",
            source_product_id=f"ITEM-{i}",
            title=f"Garment {i}",
            category="tops",
            price_minor=100000,
        )
        for i in range(15)
    ]
    adapter = PartnerFeedAdapter(feed_items=items)

    # First page
    batch1 = await adapter.fetch_batch(cursor=None, limit=10)
    assert len(batch1.products) == 10
    assert batch1.has_more is True
    assert batch1.cursor == "10"

    # Second page
    batch2 = await adapter.fetch_batch(cursor=batch1.cursor, limit=10)
    assert len(batch2.products) == 5
    assert batch2.has_more is False
    assert batch2.cursor is None


@pytest.mark.asyncio
async def test_store_adapters_initialization_and_slugs() -> None:
    amazon = AmazonAdapter()
    assert amazon.source_slug == "amazon"

    myntra = MyntraAdapter()
    assert myntra.source_slug == "myntra"

    flipkart = FlipkartAdapter()
    assert flipkart.source_slug == "flipkart"


@pytest.mark.asyncio
async def test_circuit_breaker_behavior() -> None:
    class FailingAdapter(BaseSourceAdapter):
        def __init__(self, config: SourceConfig) -> None:
            super().__init__(config)
            self.call_count = 0

        async def _fetch_batch_impl(self, cursor: str | None, limit: int) -> AcquisitionBatch:
            self.call_count += 1
            raise ConnectionError("Upstream API unreachable")

    cfg = SourceConfig(
        source_slug="failing-source",
        name="Failing Source",
        circuit_breaker_threshold=3,
        circuit_breaker_cooldown_seconds=0.2,
        max_rps=0,
    )
    adapter = FailingAdapter(cfg)

    # First 3 failures should trigger circuit breaker
    for _ in range(3):
        with pytest.raises(ConnectionError):
            await adapter.fetch_batch()

    assert adapter.circuit_state == "OPEN"

    # Next call should fail immediately with CircuitBreakerOpenError without invoking _fetch_batch_impl
    with pytest.raises(CircuitBreakerOpenError, match="Circuit breaker is OPEN"):
        await adapter.fetch_batch()

    assert adapter.call_count == 3  # not incremented on blocked call

    # Wait for cooldown
    time.sleep(0.25)
    assert adapter.circuit_state == "HALF_OPEN"
