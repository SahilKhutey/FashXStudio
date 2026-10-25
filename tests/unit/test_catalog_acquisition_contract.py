"""Unit tests for catalog acquisition contracts, DTOs, and registry."""

import pytest

from fashx.catalog.acquisition.contract import AcquisitionBatch, SourceProduct
from fashx.catalog.acquisition.registry import AdapterRegistry, SourceConfig


def test_source_product_immutability_and_defaults() -> None:
    p = SourceProduct(
        source_slug="amazon",
        source_product_id="B001",
        title="Linen Shirt",
        category="tops",
        price_minor=149900,
        currency="INR",
        product_url="https://amazon.in/dp/B001",
    )
    assert p.source_slug == "amazon"
    assert p.source_product_id == "B001"
    assert p.price_minor == 149900
    assert p.currency == "INR"
    assert p.in_stock is True
    assert p.sizes == ()
    assert p.image_rights == "partner_authorized"
    assert p.tryon_rights is False

    # Immutability check
    with pytest.raises(AttributeError):
        p.title = "New Title"  # type: ignore[misc]


def test_acquisition_batch_properties() -> None:
    p1 = SourceProduct(
        source_slug="myntra",
        source_product_id="MYN-1",
        title="Cotton Tee",
        category="tops",
        price_minor=79900,
    )
    batch = AcquisitionBatch(
        source_slug="myntra",
        products=[p1],
        cursor="next-123",
        has_more=True,
        total_found=100,
    )
    assert batch.source_slug == "myntra"
    assert len(batch.products) == 1
    assert batch.cursor == "next-123"
    assert batch.has_more is True
    assert batch.total_found == 100


def test_adapter_registry_lifecycle() -> None:
    registry = AdapterRegistry()
    assert registry.list_sources() == []

    class DummyAdapter:
        source_slug = "dummy"

        async def fetch_batch(self, cursor=None, limit=100):
            return AcquisitionBatch(source_slug="dummy", products=[])

    adapter = DummyAdapter()
    config = SourceConfig(source_slug="dummy", name="Dummy Store", max_rps=5.0)

    # Register
    registry.register(adapter, config)
    assert registry.list_sources() == ["dummy"]
    assert registry.get("dummy") is adapter
    assert registry.get_config("dummy") == config

    # Missing lookup
    with pytest.raises(KeyError, match="No catalog adapter registered"):
        registry.get("non-existent")

    # Unregister
    registry.unregister("dummy")
    assert registry.list_sources() == []
