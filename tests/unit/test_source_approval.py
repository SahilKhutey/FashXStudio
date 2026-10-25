"""Tests for source registration, approval lifecycle, and fail-closed security guards."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from database.models.catalog import CatalogSource, Merchant
from fashx.catalog.acquisition.contract import AcquisitionBatch, SourceProduct
from fashx.catalog.acquisition.pipeline import AcquisitionPipeline
from fashx.catalog.eligibility import evaluate_eligibility
from fashx.catalog.repositories.catalog_repository import CatalogUnitOfWork


@pytest.mark.asyncio
async def test_unregistered_source_fails_closed(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Acquisition pipeline must reject unregistered sources without writing or clearing records."""
    uow = CatalogUnitOfWork(session_factory)
    pipeline = AcquisitionPipeline(uow)

    batch = AcquisitionBatch(
        source_slug="unregistered-vendor",
        products=[
            SourceProduct(
                source_slug="unregistered-vendor",
                source_product_id="P-001",
                title="Unregistered Shirt",
                product_url="https://vendor.com/shirt",
                category="tops",
                price_minor=99900,
                brand="VendorBrand",
            )
        ],
    )
    report = await pipeline.process_batch(batch, apply=True)
    assert report.success is False
    assert report.total_products == 1
    assert report.rejected == 1
    assert any("unregistered_source" in k for k in report.rejection_reasons)


@pytest.mark.asyncio
async def test_pending_and_suspended_sources_rejected_from_ingestion(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Sources in draft, pending, or suspended status must be refused batch ingestion."""
    uow = CatalogUnitOfWork(session_factory)
    async with uow:
        merchant = Merchant(name="Suspended Retailer", merchant_type="retailer")
        suspended_source = CatalogSource(
            slug="store-suspended",
            name="Suspended Retailer",
            kind="api",
            status="suspended",
            rights_display=False,
            rights_tryon=False,
            image_policy="mirror",
        )
        pending_source = CatalogSource(
            slug="store-pending",
            name="Pending Retailer",
            kind="api",
            status="pending",
            rights_display=False,
            rights_tryon=False,
            image_policy="mirror",
        )
        uow.merchants.add(merchant)
        uow.sources.add(suspended_source)
        uow.sources.add(pending_source)
        await uow.commit()

    pipeline = AcquisitionPipeline(uow)

    # 1. Suspended source attempt
    batch_suspended = AcquisitionBatch(
        source_slug="store-suspended",
        products=[
            SourceProduct(
                source_slug="store-suspended",
                source_product_id="SKU-SUS-1",
                title="Suspended Top",
                product_url="https://merchant.com/1",
                category="tops",
                price_minor=129900,
                brand="SuspendedBrand",
            )
        ],
    )
    res_suspended = await pipeline.process_batch(batch_suspended, apply=True)
    assert res_suspended.success is False
    assert res_suspended.rejected == 1
    assert any("source_not_cleared" in k for k in res_suspended.rejection_reasons)

    # 2. Pending source attempt
    batch_pending = AcquisitionBatch(
        source_slug="store-pending",
        products=[
            SourceProduct(
                source_slug="store-pending",
                source_product_id="SKU-PEN-1",
                title="Pending Top",
                product_url="https://merchant.com/2",
                category="tops",
                price_minor=149900,
                brand="PendingBrand",
            )
        ],
    )
    res_pending = await pipeline.process_batch(batch_pending, apply=True)
    assert res_pending.success is False
    assert res_pending.rejected == 1
    assert any("source_not_cleared" in k for k in res_pending.rejection_reasons)


@pytest.mark.asyncio
async def test_cleared_source_permitted_for_ingestion(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Only cleared sources with verified status can proceed with acquisition."""
    uow = CatalogUnitOfWork(session_factory)
    async with uow:
        merchant = Merchant(name="Cleared Partner", merchant_type="brand")
        cleared_source = CatalogSource(
            slug="partner-cleared",
            name="Cleared Partner",
            kind="partner_feed",
            status="cleared",
            rights_display=True,
            rights_tryon=True,
            image_policy="mirror",
        )
        uow.merchants.add(merchant)
        uow.sources.add(cleared_source)
        await uow.commit()

    pipeline = AcquisitionPipeline(uow)
    batch = AcquisitionBatch(
        source_slug="partner-cleared",
        products=[
            SourceProduct(
                source_slug="partner-cleared",
                source_product_id="SKU-CLR-1",
                title="Premium Silk Shirt",
                product_url="https://cleared.example.com/items/1",
                category="tops",
                price_minor=249900,
                brand="ClearedBrand",
                in_stock=True,
            )
        ],
    )
    report = await pipeline.process_batch(batch, apply=True)
    assert report.success is True
    assert report.inserted == 1
    assert report.rejected == 0


def test_unapproved_source_fails_capability_evaluator() -> None:
    """CatalogEligibility evaluation fails closed on all capabilities when source_cleared is False."""
    elig = evaluate_eligibility(
        source_cleared=False,
        display_rights=True,
        image_validated=True,
        tryon_rights=True,
        stock_known=True,
        in_stock=True,
        product_url_valid=True,
        category_valid=True,
    )
    assert elig.discoverable is False
    assert elig.image_displayable is False
    assert elig.tryon_allowed is False
    assert elig.purchasable is False
    assert "Source is not approved for ingestion" in elig.reasons
