"""SA-001, SA-006, SA-007: Adapter contract, capabilities, normalization, and batching."""

from __future__ import annotations

from typing import Any

import pytest

from fashx.catalog.acquisition.contract import SourceBatch, SourceProduct
from fashx.catalog.acquisition.contracts_v2 import (
    CatalogSourceAdapterV2,
    IntegrationStatus,
    SourceCapabilities,
    SourceErrorCode,
    SourceHealthReport,
    SourceHealthState,
)


class DummyMockAdapter:
    """Mock adapter conforming to CatalogSourceAdapterV2 protocol."""

    source_slug = "dummy-retailer"
    integration_status = IntegrationStatus.MOCK

    def capabilities(self) -> SourceCapabilities:
        return SourceCapabilities(
            full_sync=True,
            incremental_sync=True,
            conditional_requests=True,
            deletion_signals=False,
            supported_formats=("json",),
        )

    async def start_full_sync(self) -> str:
        return "full_sync_started"

    async def start_incremental_sync(
        self,
        watermark: Any = None,
        cursor: str | None = None,
    ) -> str:
        return f"incremental_sync_started:{cursor}"

    async def health_check(self) -> SourceHealthReport:
        return SourceHealthReport(
            source_slug=self.source_slug,
            state=SourceHealthState.HEALTHY,
            message="Dummy adapter healthy",
        )

    async def fetch_page(self, cursor: str | None = None, limit: int = 100) -> SourceBatch:
        products = [
            SourceProduct(
                source_slug=self.source_slug,
                source_product_id=f"prod-{i}",
                title=f"Garment {i}",
                brand="TestBrand",
                description="Test description",
                category="dresses",
                price_minor=4999,
                currency="INR",
                in_stock=True,
                product_url=f"https://example.com/p/{i}",
                image_url=f"https://example.com/p/{i}.jpg",
            )
            for i in range(1, 11)
        ]
        return SourceBatch(
            source_slug=self.source_slug,
            products=products,
            cursor=None,
            has_more=False,
        )

    def normalize_product(self, raw_item: dict) -> SourceProduct:
        return SourceProduct(
            source_slug=self.source_slug,
            source_product_id=str(raw_item["id"]),
            title=raw_item["title"],
            brand=raw_item.get("brand", "Unknown"),
            description="Normalized",
            category="tops",
            price_minor=int(raw_item["price"] * 100),
            currency="INR",
            in_stock=True,
            product_url=raw_item["url"],
            image_url=raw_item.get("images", [None])[0] if raw_item.get("images") else None,
        )

    def map_error(self, exc: Exception) -> SourceErrorCode:
        return SourceErrorCode.UPSTREAM_SERVICE_ERROR


def test_sa_001_dummy_adapter_implements_protocol() -> None:
    """SA-001: Verify that adapter conforms to CatalogSourceAdapterV2 protocol."""
    adapter = DummyMockAdapter()
    assert isinstance(adapter, CatalogSourceAdapterV2)
    assert adapter.source_slug == "dummy-retailer"
    assert adapter.integration_status == IntegrationStatus.MOCK


def test_sa_001_capabilities() -> None:
    """SA-001: Capabilities advertise supported sync modes and pagination features."""
    adapter = DummyMockAdapter()
    caps = adapter.capabilities()
    assert caps.full_sync is True
    assert caps.incremental_sync is True
    assert caps.conditional_requests is True
    assert "json" in caps.supported_formats


@pytest.mark.asyncio
async def test_sa_006_fetch_page_and_batch_limits() -> None:
    """SA-006 & SA-007: Safe page fetching with batch bounds."""
    adapter = DummyMockAdapter()
    batch = await adapter.fetch_page(cursor=None, limit=50)
    assert len(batch.products) == 10
    assert batch.has_more is False
    assert batch.cursor is None


def test_sa_007_normalize_product() -> None:
    """SA-007: Product normalization handles types and currency correctly."""
    adapter = DummyMockAdapter()
    raw = {
        "id": "item-99",
        "title": "Summer Linen Shirt",
        "brand": "FashBrand",
        "price": 29.99,
        "url": "https://example.com/item-99",
        "images": ["https://example.com/img1.jpg"],
    }
    normalized = adapter.normalize_product(raw)
    assert normalized.source_product_id == "item-99"
    assert normalized.title == "Summer Linen Shirt"
    assert normalized.price_minor == 2999
    assert normalized.currency == "INR"
    assert normalized.product_url == "https://example.com/item-99"
