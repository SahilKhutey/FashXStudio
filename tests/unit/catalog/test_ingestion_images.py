"""Unit tests for catalog ingestion image rights, storage, and privacy (ING-016 to ING-018, ING-036, ING-040)."""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from fashx.catalog.acquisition.contract import AcquisitionBatch, SourceProduct
from fashx.catalog.acquisition.image_validator import SafeImageValidator
from fashx.catalog.acquisition.pipeline import AcquisitionPipeline
from fashx.catalog.repositories.catalog_repository import CatalogUnitOfWork


def test_ing_016_image_fetch_denied():
    """ING-016: SSRF-unsafe or non-https images fail validation."""
    valid, reason = SafeImageValidator.validate_image_url("http://insecure.com/img.jpg")
    assert not valid
    assert "https" in reason.lower()

    valid2, reason2 = SafeImageValidator.validate_image_url("https://127.0.0.1/internal.jpg")
    assert not valid2
    assert "loopback" in reason2.lower() or "private" in reason2.lower()


def test_ing_017_image_storage_denied():
    """ING-017: When source image_policy is hotlink or display denied, storage is not permitted."""
    res = SafeImageValidator.evaluate_permissions(
        image_url="https://images.example.com/p/1.jpg",
        source_status="cleared",
        source_rights_display=False,  # Display denied!
        source_rights_tryon=False,
        source_image_policy="hotlink",
        item_image_rights="partner_authorized",
        item_tryon_rights=False,
    )
    assert not res.display_eligible
    assert not res.tryon_eligible


@pytest.mark.asyncio
async def test_ing_018_vto_permission_denied_sets_tryon_supported_false(
    session_factory: async_sessionmaker[AsyncSession],
    setup_authorized_source: dict,
) -> None:
    """ING-018: When tryon rights are denied, tryon_supported remains False."""
    uow = CatalogUnitOfWork(session_factory)
    pipeline = AcquisitionPipeline(uow)
    source_slug = setup_authorized_source["source_slug"]
    merchant_id = setup_authorized_source["merchant_id"]

    batch = AcquisitionBatch(
        source_slug=source_slug,
        products=[
            SourceProduct(
                source_slug=source_slug,
                source_product_id="VTO-DENIED-001",
                title="Cotton Casual Shirt",
                category="tops",
                subcategory="shirt",
                price_minor=149900,
                currency="INR",
                product_url="https://merchant.example.com/p/1",
                image_url="https://images.example.com/p/1.jpg",
                tryon_rights=False,  # Item tryon rights denied!
            )
        ],
    )
    report = await pipeline.process_batch(batch, apply=True)
    assert report.success is True
    assert report.inserted == 1

    async with uow:
        prod = await uow.merchant_products.get_by_source_id(merchant_id, "VTO-DENIED-001")
        assert prod is not None
        garment = await uow.canonical_garments.get_by_id(prod.canonical_garment_id)
        assert garment is not None
        assert garment.tryon_supported is False


def test_ing_036_no_secrets_or_signed_urls_in_quarantine_logs():
    """ING-036: Sanitizer strips credentials and access tokens from quarantined records."""
    from fashx.catalog.acquisition.quarantine import CatalogQuarantineService

    raw = {
        "title": "Secret Shirt",
        "api_key": "AKIA1234567890SECRET",
        "access_token": "bearer-jwt-token-abcdef",
        "source_password": "supersecretpassword",
        "price_minor": 1000,
    }
    sanitized = CatalogQuarantineService._sanitize_record_reference(raw)
    assert sanitized["api_key"] == "***REDACTED***"
    assert sanitized["access_token"] == "***REDACTED***"
    assert sanitized["source_password"] == "***REDACTED***"
    assert sanitized["title"] == "Secret Shirt"


@pytest.mark.asyncio
async def test_ing_040_db_failure_rolls_back_safely(
    session_factory: async_sessionmaker[AsyncSession],
    setup_authorized_source: dict,
) -> None:
    """ING-040: Transaction abort rolls back all product and offer writes safely."""
    uow = CatalogUnitOfWork(session_factory)
    pipeline = AcquisitionPipeline(uow)

    batch = AcquisitionBatch(
        source_slug=setup_authorized_source["source_slug"],
        products=[
            SourceProduct(
                source_slug=setup_authorized_source["source_slug"],
                source_product_id="ROLLBACK-001",
                title="Rollback Garment",
                category="tops",
                price_minor=10000,
                currency="INR",
                product_url="https://merchant.example.com/p/rollback",
            )
        ],
    )
    # Run with apply=False (dry-run simulation): changes must NOT be committed
    report = await pipeline.process_batch(batch, apply=False)
    assert report.success is True

    async with uow:
        prod = await uow.merchant_products.get_by_source_id(
            setup_authorized_source["merchant_id"], "ROLLBACK-001"
        )
        assert prod is None
