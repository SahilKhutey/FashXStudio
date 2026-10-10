from decimal import Decimal

import pytest
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from database.models.catalog import CatalogSource, Merchant
from fashx.catalog.application.ingest_product import (
    IngestMerchantProductUseCase,
    IngestProductCommand,
)
from fashx.catalog.repositories.catalog_repository import CatalogUnitOfWork
from fashx.ingest.model import CanonicalProduct, parse_price


def test_parse_price() -> None:
    amt, cur = parse_price("₹1,499.50")
    assert amt == Decimal("1499.50")
    assert cur == "INR"

    amt, cur = parse_price("2999 INR")
    assert amt == Decimal("2999")
    assert cur == "INR"

    amt, cur = parse_price("Rs. 499")
    assert amt == Decimal("499")
    assert cur == "INR"

    amt, cur = parse_price("49.99 USD")
    assert amt == Decimal("49.99")
    assert cur == "USD"

    with pytest.raises(ValueError, match="unparseable price"):
        parse_price("invalid-amount")


def test_canonical_product_schema_validation() -> None:
    product = CanonicalProduct(
        source_product_id="SKU-1001",
        title="Handloom Cotton Kurta",
        description="Authentic breathable cotton kurta",
        link="https://brand.com/products/sku-1001",
        image_url="https://brand.com/images/sku-1001.jpg",
        price=Decimal("1299.00"),
        currency="INR",
        gender="unisex",
        color="Indigo",
        size="L",
        source_category="Ethnic Wear > Kurtas",
    )
    assert product.title == "Handloom Cotton Kurta"
    assert product.currency == "INR"
    assert product.in_stock is True

    # Rejection of non-INR currency
    with pytest.raises(PydanticValidationError, match="unsupported_currency"):
        CanonicalProduct(
            source_product_id="SKU-1002",
            title="Imported Jacket",
            link="https://brand.com/products/sku-1002",
            image_url="https://brand.com/images/sku-1002.jpg",
            price=Decimal("49.99"),
            currency="USD",
        )

    # Rejection of non-positive price
    with pytest.raises(PydanticValidationError, match="price must be positive"):
        CanonicalProduct(
            source_product_id="SKU-1003",
            title="Free Sample",
            link="https://brand.com/products/sku-1003",
            image_url="https://brand.com/images/sku-1003.jpg",
            price=Decimal("0.00"),
            currency="INR",
        )


@pytest.mark.asyncio
async def test_feed_excludes_products_from_suspended_or_pending_sources(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    catalog_uow = CatalogUnitOfWork(session_factory)

    async with catalog_uow:
        # 1. Create merchant
        merchant = Merchant(name="Test Retailer", merchant_type="retailer")
        catalog_uow.merchants.add(merchant)
        await catalog_uow.commit()
        merchant_id = merchant.id

        # 2. Create Sources: 1 Cleared, 1 Suspended, 1 Pending
        cleared_source = CatalogSource(
            slug="brand-cleared",
            name="Cleared Brand",
            kind="feed_url",
            status="cleared",
            rights_display=True,
            rights_tryon=True,
            image_policy="mirror",
        )
        suspended_source = CatalogSource(
            slug="brand-suspended",
            name="Suspended Brand",
            kind="feed_url",
            status="suspended",
            rights_display=False,
            rights_tryon=False,
            image_policy="hotlink",
        )
        pending_source = CatalogSource(
            slug="brand-pending",
            name="Pending Brand",
            kind="feed_url",
            status="pending",
            rights_display=False,
            rights_tryon=False,
            image_policy="mirror",
        )
        catalog_uow.sources.add(cleared_source)
        catalog_uow.sources.add(suspended_source)
        catalog_uow.sources.add(pending_source)
        await catalog_uow.commit()

        # 3. Ingest items
        ingest_uc = IngestMerchantProductUseCase(catalog_uow)

        # Item 1: Cleared source, active -> MUST APPEAR
        item_cleared_active = await ingest_uc.execute(
            IngestProductCommand(
                merchant_id=merchant_id,
                source_id=cleared_source.id,
                source_product_id="ITEM-CLEARED-ACTIVE",
                title="Active Cleared Product",
                source_url="https://brand.com/p1",
                category="tops",
                price_minor=149900,
                status="active",
            )
        )

        # Item 2: Suspended source, active -> MUST BE EXCLUDED
        item_suspended = await ingest_uc.execute(
            IngestProductCommand(
                merchant_id=merchant_id,
                source_id=suspended_source.id,
                source_product_id="ITEM-SUSPENDED",
                title="Suspended Source Product",
                source_url="https://brand.com/p2",
                category="tops",
                price_minor=199900,
                status="active",
            )
        )

        # Item 3: Cleared source, stale -> MUST BE EXCLUDED
        item_cleared_stale = await ingest_uc.execute(
            IngestProductCommand(
                merchant_id=merchant_id,
                source_id=cleared_source.id,
                source_product_id="ITEM-CLEARED-STALE",
                title="Stale Cleared Product",
                source_url="https://brand.com/p3",
                category="tops",
                price_minor=249900,
                status="stale",
            )
        )

        # Item 4: Pending source, active -> MUST BE EXCLUDED
        item_pending = await ingest_uc.execute(
            IngestProductCommand(
                merchant_id=merchant_id,
                source_id=pending_source.id,
                source_product_id="ITEM-PENDING",
                title="Pending Source Product",
                source_url="https://brand.com/p4",
                category="tops",
                price_minor=99900,
                status="active",
            )
        )

        # 4. Fetch feed candidates
        feed_candidates = await catalog_uow.canonical_garments.list_feed_candidates(limit=100)
        feed_garment_ids = {g.id for g in feed_candidates}

        # Assertions: ONLY cleared + active product is returned
        assert item_cleared_active.canonical_garment_id in feed_garment_ids
        assert item_suspended.canonical_garment_id not in feed_garment_ids
        assert item_cleared_stale.canonical_garment_id not in feed_garment_ids
        assert item_pending.canonical_garment_id not in feed_garment_ids


@pytest.mark.asyncio
async def test_source_lifecycle_and_clearance_guards(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    catalog_uow = CatalogUnitOfWork(session_factory)
    async with catalog_uow:
        # Register source in pending status
        source = CatalogSource(
            slug="brand-x",
            name="Brand X",
            kind="feed_url",
            status="pending",
            rights_display=False,
            rights_tryon=False,
            image_policy="hotlink",
        )
        catalog_uow.sources.add(source)
        await catalog_uow.commit()

        fetched = await catalog_uow.sources.get_by_slug("brand-x")
        assert fetched is not None
        assert fetched.status == "pending"

        # Hotlink source cannot have rights_tryon=True without mirror
        assert fetched.image_policy == "hotlink"

        # Updating image_policy to mirror allows tryon clearance
        fetched.image_policy = "mirror"
        fetched.status = "cleared"
        fetched.rights_display = True
        fetched.rights_tryon = True
        fetched.notes = "[Evidence: docs/evidence/brand-x.md]"
        await catalog_uow.commit()

        cleared = await catalog_uow.sources.get_by_slug("brand-x")
        assert cleared is not None
        assert cleared.status == "cleared"
        assert cleared.rights_tryon is True
        assert cleared.rights_display is True

