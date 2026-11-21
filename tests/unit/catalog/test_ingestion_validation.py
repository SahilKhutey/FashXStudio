"""Unit tests for catalog ingestion record validation (ING-007 to ING-015, ING-038)."""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from fashx.catalog.acquisition.contract import AcquisitionBatch, SourceProduct
from fashx.catalog.acquisition.normalizer import CatalogNormalizer, to_minor_units
from fashx.catalog.acquisition.pipeline import AcquisitionPipeline
from fashx.catalog.acquisition.record_validation import (
    normalize_source_product_id,
    normalize_title,
    validate_product_record,
)
from fashx.catalog.repositories.catalog_repository import CatalogUnitOfWork


def test_ing_007_missing_product_id_rejected():
    """ING-007: Empty or whitespace-only product ID raises ValueError."""
    with pytest.raises(ValueError, match="missing_source_product_id"):
        normalize_source_product_id("")
    with pytest.raises(ValueError, match="missing_source_product_id"):
        normalize_source_product_id("   ")

    # Preserves case
    assert normalize_source_product_id("SKU-100") == "SKU-100"
    assert normalize_source_product_id("sku-100") == "sku-100"


def test_ing_008_missing_title_rejected():
    """ING-008: Empty, whitespace, or too-short title raises ValueError."""
    with pytest.raises(ValueError, match="missing_title"):
        normalize_title("")
    with pytest.raises(ValueError, match="title_too_short"):
        normalize_title("A")

    assert normalize_title("  Cotton Casual Shirt  ") == "Cotton Casual Shirt"


def test_ing_009_unknown_category_not_mapped_to_shirt():
    """ING-009: Unknown category returns mapped=False and is NOT silently mapped to tops/shirt."""
    res = CatalogNormalizer.normalize_category_result("kitchenware", "blender")
    assert res.mapped is False
    assert res.category is None

    res2 = CatalogNormalizer.normalize_category_result("electronics", "smartphone")
    assert res2.mapped is False
    assert res2.category is None

    # Recognized category maps cleanly
    res3 = CatalogNormalizer.normalize_category_result("men's jeans")
    assert res3.mapped is True
    assert res3.category == "bottoms"
    assert res3.subcategory == "jeans"


def test_ing_010_unsupported_currency_rejected():
    """ING-010: Unsupported currencies raise ValueError."""
    with pytest.raises(ValueError, match="unsupported_currency"):
        to_minor_units("100.00", "XYZ")
    with pytest.raises(ValueError, match="unsupported_currency"):
        to_minor_units("100.00", "BITCOIN")


def test_ing_011_negative_or_zero_price_rejected():
    """ING-011: Negative and zero prices raise ValueError."""
    with pytest.raises(ValueError, match="price_must_be_positive_and_finite"):
        to_minor_units("-1499.00", "INR")
    with pytest.raises(ValueError, match="price_must_be_positive_and_finite"):
        to_minor_units("0", "INR")


def test_ing_012_decimal_price_conversion():
    """ING-012: Decimal prices convert to exact minor currency units."""
    assert to_minor_units("1499.50", "INR") == 149950
    assert to_minor_units("999.00", "INR") == 99900
    assert to_minor_units("15.99", "USD") == 1599
    assert to_minor_units("1499", "JPY") == 1499  # JPY exponent 0


def test_ing_013_invalid_product_url_validation():
    """ING-013: Invalid schemes or embedded credentials fail URL validation."""

    class FakeProduct:
        source_product_id = "P1"
        title = "Polo Shirt"
        currency = "INR"
        price_minor = 1000
        category = "tops"
        product_url = "http://insecure-http.com/p1"  # Not HTTPS

    res = validate_product_record(FakeProduct())
    assert not res.valid
    assert any(i.code == "invalid_product_url" for i in res.issues)

    FakeProduct.product_url = "https://user:password@merchant.com/p1"  # Embedded credentials
    res2 = validate_product_record(FakeProduct())
    assert not res2.valid
    assert any(i.code == "invalid_product_url" for i in res2.issues)


def test_ing_014_unapproved_product_domain():
    """ING-014: URLs not in allowed_hosts fail validation."""

    class FakeProduct:
        source_product_id = "P1"
        title = "Polo Shirt"
        currency = "INR"
        price_minor = 1000
        category = "tops"
        product_url = "https://malicious-redirect.com/p1"

    res = validate_product_record(FakeProduct(), allowed_hosts={"approved-merchant.com"})
    assert not res.valid
    assert any(i.code == "unapproved_domain" for i in res.issues)


@pytest.mark.asyncio
async def test_ing_015_missing_image_url_still_ingests_metadata(
    session_factory: async_sessionmaker[AsyncSession],
    setup_authorized_source: dict,
) -> None:
    """ING-015: When image_url is missing, product metadata is still valid and ingested."""
    uow = CatalogUnitOfWork(session_factory)
    pipeline = AcquisitionPipeline(uow)

    batch = AcquisitionBatch(
        source_slug=setup_authorized_source["source_slug"],
        products=[
            SourceProduct(
                source_slug=setup_authorized_source["source_slug"],
                source_product_id="NO-IMG-001",
                title="Cotton Chino Trousers",
                category="bottoms",
                subcategory="trousers",
                price_minor=199900,
                currency="INR",
                product_url="https://merchant.example.com/p/no-img",
                image_url=None,  # No image!
            )
        ],
    )
    report = await pipeline.process_batch(batch, apply=True)
    assert report.success is True
    assert report.inserted == 1
    assert report.image_counts["missing"] == 1

    # Verify garment created with tryon_supported=False
    async with uow:
        prod = await uow.merchant_products.get_by_source_id(
            setup_authorized_source["merchant_id"], "NO-IMG-001"
        )
        assert prod is not None
        assert prod.canonical_garment_id is not None
        garment = await uow.canonical_garments.get_by_id(prod.canonical_garment_id)
        assert garment is not None
        assert garment.tryon_supported is False


@pytest.mark.asyncio
async def test_ing_038_missing_stock_defaults_to_unknown(
    session_factory: async_sessionmaker[AsyncSession],
    setup_authorized_source: dict,
) -> None:
    """ING-038: Missing stock field is handled safely without crashing."""
    uow = CatalogUnitOfWork(session_factory)
    pipeline = AcquisitionPipeline(uow)

    batch = AcquisitionBatch(
        source_slug=setup_authorized_source["source_slug"],
        products=[
            SourceProduct(
                source_slug=setup_authorized_source["source_slug"],
                source_product_id="STOCK-UNKNOWN-001",
                title="Summer Linen Dress",
                category="dresses",
                subcategory="dress",
                price_minor=249900,
                currency="INR",
                product_url="https://merchant.example.com/p/dress-1",
                in_stock=None,  # Stock unknown!
            )
        ],
    )
    report = await pipeline.process_batch(batch, apply=True)
    assert report.success is True
    assert report.inserted == 1
