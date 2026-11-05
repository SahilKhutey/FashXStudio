from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from database.models import Base
from database.models.catalog import CanonicalGarment, Merchant, MerchantOffer
from fashx.catalog.customer_router import _resolve_garment_detail
from fashx.catalog.repositories.catalog_repository import CatalogUnitOfWork
from fashx.core.errors import EntityNotFoundError


@pytest.fixture
async def db_session_factory():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    yield factory
    await engine.dispose()


@pytest.mark.asyncio
async def test_rc06_offer_sorting_and_display_price(db_session_factory):
    uow = CatalogUnitOfWork(db_session_factory)
    garment_id = uuid4()
    merchant_1 = uuid4()
    merchant_2 = uuid4()
    merchant_3 = uuid4()

    sync_time = datetime(2026, 11, 4, 8, 30, tzinfo=UTC)

    async with uow:
        uow.merchants.add(Merchant(id=merchant_1, name="Amazon", merchant_type="retailer"))
        uow.merchants.add(Merchant(id=merchant_2, name="Myntra", merchant_type="retailer"))
        uow.merchants.add(Merchant(id=merchant_3, name="Flipkart", merchant_type="retailer"))

        garment = CanonicalGarment(
            id=garment_id,
            display_name="Silk Summer Shirt",
            category="tops",
            subcategory="shirts",
            active=True,
            price_minor=250000,
        )
        uow.canonical_garments.add(garment)

        # Offer 1: Out of stock, cheaper price (₹1,500)
        uow.offers.add(
            MerchantOffer(
                id=uuid4(),
                garment_id=garment_id,
                merchant_id=merchant_1,
                source_product_id="AMZ-001",
                url="https://amazon.in/p/1",
                price_minor=150000,
                currency="INR",
                in_stock=False,
                last_synced_at=sync_time,
            )
        )
        # Offer 2: In stock, higher price (₹2,200)
        uow.offers.add(
            MerchantOffer(
                id=uuid4(),
                garment_id=garment_id,
                merchant_id=merchant_2,
                source_product_id="MYN-001",
                url="https://myntra.com/p/2",
                price_minor=220000,
                currency="INR",
                in_stock=True,
                last_synced_at=sync_time,
            )
        )
        # Offer 3: In stock, lowest in-stock price (₹1,800)
        uow.offers.add(
            MerchantOffer(
                id=uuid4(),
                garment_id=garment_id,
                merchant_id=merchant_3,
                source_product_id="FLP-001",
                url="https://flipkart.com/p/3",
                price_minor=180000,
                currency="INR",
                in_stock=True,
                last_synced_at=sync_time,
            )
        )
        await uow.commit()

    detail = await _resolve_garment_detail(garment_id, uow)

    # 1. Display price should be lowest IN-STOCK offer (₹1,800 = 180000)
    assert detail.price_minor == 180000
    assert detail.currency == "INR"

    # 2. Offers list should sort in-stock first, then ascending by price
    # Offer 3 (180000 in-stock) -> Offer 2 (220000 in-stock) -> Offer 1 (150000 out-of-stock)
    assert len(detail.offers) == 3
    assert detail.offers[0].source_product_id == "FLP-001"
    assert detail.offers[0].in_stock is True
    assert detail.offers[0].price_minor == 180000
    assert detail.offers[0].merchant_name == "Flipkart"
    assert detail.offers[0].updated_at is not None
    assert detail.offers[0].updated_at.year == 2026

    assert detail.offers[1].source_product_id == "MYN-001"
    assert detail.offers[1].in_stock is True
    assert detail.offers[1].price_minor == 220000
    assert detail.offers[1].merchant_name == "Myntra"

    assert detail.offers[2].source_product_id == "AMZ-001"
    assert detail.offers[2].in_stock is False
    assert detail.offers[2].price_minor == 150000
    assert detail.offers[2].merchant_name == "Amazon"


@pytest.mark.asyncio
async def test_rc06_display_price_all_out_of_stock(db_session_factory):
    uow = CatalogUnitOfWork(db_session_factory)
    garment_id = uuid4()
    merchant_id = uuid4()

    async with uow:
        uow.merchants.add(Merchant(id=merchant_id, name="Store", merchant_type="retailer"))
        garment = CanonicalGarment(
            id=garment_id,
            display_name="Winter Coat",
            category="outerwear",
            active=True,
            price_minor=800000,
        )
        uow.canonical_garments.add(garment)

        # Only an out-of-stock offer
        uow.offers.add(
            MerchantOffer(
                id=uuid4(),
                garment_id=garment_id,
                merchant_id=merchant_id,
                source_product_id="COAT-1",
                url="https://store.com/coat",
                price_minor=750000,
                currency="INR",
                in_stock=False,
            )
        )
        await uow.commit()

    detail = await _resolve_garment_detail(garment_id, uow)
    # When no in-stock offer, falls back to best offer price (750000)
    assert detail.price_minor == 750000


@pytest.mark.asyncio
async def test_rc06_display_price_no_offers(db_session_factory):
    uow = CatalogUnitOfWork(db_session_factory)
    garment_id = uuid4()

    async with uow:
        garment = CanonicalGarment(
            id=garment_id,
            display_name="Simple Tee",
            category="tops",
            active=True,
            price_minor=49900,
        )
        uow.canonical_garments.add(garment)
        await uow.commit()

    detail = await _resolve_garment_detail(garment_id, uow)
    # Falls back to garment's price_minor
    assert detail.price_minor == 49900
    assert detail.currency == "INR"
    assert detail.offers == []


@pytest.mark.asyncio
async def test_rc06_inactive_garment_not_found(db_session_factory):
    uow = CatalogUnitOfWork(db_session_factory)
    garment_id = uuid4()

    async with uow:
        garment = CanonicalGarment(
            id=garment_id,
            display_name="Hidden Dress",
            category="dresses",
            active=False,  # Inactive
            price_minor=99900,
        )
        uow.canonical_garments.add(garment)
        await uow.commit()

    with pytest.raises(EntityNotFoundError):
        await _resolve_garment_detail(garment_id, uow)
