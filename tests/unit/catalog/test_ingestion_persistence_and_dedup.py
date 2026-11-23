"""Unit tests for product persistence, deduplication, and update semantics (ING-019 to ING-026, ING-028 to ING-030)."""

from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from database.models.catalog import CatalogSource, Merchant
from fashx.catalog.acquisition.contract import AcquisitionBatch, SourceProduct
from fashx.catalog.acquisition.pipeline import AcquisitionPipeline
from fashx.catalog.repositories.catalog_repository import CatalogUnitOfWork


@pytest.mark.asyncio
async def test_ing_019_to_023_insert_unchanged_update_and_dedup(
    session_factory: async_sessionmaker[AsyncSession],
    setup_authorized_source: dict,
) -> None:
    """ING-019, 020, 021, 022, 023: Verify insert, unchanged, price update, title update, and no duplicates."""
    uow = CatalogUnitOfWork(session_factory)
    pipeline = AcquisitionPipeline(uow)
    source_slug = setup_authorized_source["source_slug"]
    merchant_id = setup_authorized_source["merchant_id"]

    item = SourceProduct(
        source_slug=source_slug,
        source_product_id="SKU-DEDUP-100",
        title="Linen Casual Shirt",
        brand="Retail Brand",
        category="tops",
        subcategory="shirt",
        price_minor=149900,
        currency="INR",
        product_url="https://merchant.example.com/p/100",
        image_url="https://images.example.com/p/100.jpg",
        in_stock=True,
        sizes=("M", "L"),
        tryon_rights=True,
    )

    # 1. ING-019: First ingestion -> INSERT
    batch1 = AcquisitionBatch(source_slug=source_slug, products=[item])
    rep1 = await pipeline.process_batch(batch1, apply=True)
    assert rep1.inserted == 1
    assert rep1.updated == 0
    assert rep1.unchanged == 0

    # 2. ING-020 & ING-023: Repeated ingestion -> UNCHANGED, no duplicate
    rep2 = await pipeline.process_batch(batch1, apply=True)
    assert rep2.inserted == 0
    assert rep2.updated == 0
    assert rep2.unchanged == 1

    # Verify single product in DB
    canonical_garment_id = None
    async with uow:
        prod = await uow.merchant_products.get_by_source_id(merchant_id, "SKU-DEDUP-100")
        assert prod is not None
        assert prod.title == "Linen Casual Shirt"
        canonical_garment_id = prod.canonical_garment_id

    # 3. ING-021: Changed price -> UPDATE offer
    item_price_drop = SourceProduct(
        source_slug=source_slug,
        source_product_id="SKU-DEDUP-100",
        title="Linen Casual Shirt",
        brand="Retail Brand",
        category="tops",
        subcategory="shirt",
        price_minor=129900,  # Price changed
        currency="INR",
        product_url="https://merchant.example.com/p/100",
        image_url="https://images.example.com/p/100.jpg",
        in_stock=True,
        sizes=("M", "L"),
        tryon_rights=True,
    )
    rep3 = await pipeline.process_batch(
        AcquisitionBatch(source_slug=source_slug, products=[item_price_drop]), apply=True
    )
    assert rep3.inserted == 0
    assert rep3.updated == 1
    assert rep3.unchanged == 0

    async with uow:
        assert canonical_garment_id is not None
        offers = await uow.offers.list_for_garment(canonical_garment_id)
        assert len(offers) == 1
        assert offers[0].price_minor == 129900

    # 4. ING-022: Changed title -> UPDATE product & canonical garment
    item_new_title = SourceProduct(
        source_slug=source_slug,
        source_product_id="SKU-DEDUP-100",
        title="Premium Organic Linen Casual Shirt",  # Title changed
        brand="Retail Brand",
        category="tops",
        subcategory="shirt",
        price_minor=129900,
        currency="INR",
        product_url="https://merchant.example.com/p/100",
        image_url="https://images.example.com/p/100.jpg",
        in_stock=True,
        sizes=("M", "L"),
        tryon_rights=True,
    )
    rep4 = await pipeline.process_batch(
        AcquisitionBatch(source_slug=source_slug, products=[item_new_title]), apply=True
    )
    assert rep4.updated == 1

    async with uow:
        updated_prod = await uow.merchant_products.get_by_source_id(merchant_id, "SKU-DEDUP-100")
        assert updated_prod.title == "Premium Organic Linen Casual Shirt"


@pytest.mark.asyncio
async def test_ing_024_same_title_different_source_id_not_merged(
    session_factory: async_sessionmaker[AsyncSession],
    setup_authorized_source: dict,
) -> None:
    """ING-024: Products with same title but different source_product_id are distinct."""
    uow = CatalogUnitOfWork(session_factory)
    pipeline = AcquisitionPipeline(uow)
    source_slug = setup_authorized_source["source_slug"]

    item1 = SourceProduct(
        source_slug=source_slug,
        source_product_id="SKU-AAA",
        title="Blue Cotton Shirt",
        category="tops",
        subcategory="shirt",
        price_minor=99900,
        currency="INR",
        product_url="https://merchant.example.com/p/aaa",
    )
    item2 = SourceProduct(
        source_slug=source_slug,
        source_product_id="SKU-BBB",  # Different ID
        title="Blue Cotton Shirt",  # Same title!
        category="tops",
        subcategory="shirt",
        price_minor=99900,
        currency="INR",
        product_url="https://merchant.example.com/p/bbb",
    )
    batch = AcquisitionBatch(source_slug=source_slug, products=[item1, item2])
    rep = await pipeline.process_batch(batch, apply=True)
    assert rep.inserted == 2

    async with uow:
        merchant_id = setup_authorized_source["merchant_id"]
        prod1 = await uow.merchant_products.get_by_source_id(merchant_id, "SKU-AAA")
        prod2 = await uow.merchant_products.get_by_source_id(merchant_id, "SKU-BBB")
        assert prod1 is not None and prod2 is not None
        assert prod1.id != prod2.id


@pytest.mark.asyncio
async def test_ing_025_same_product_from_two_merchants_separate_offers(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """ING-025: Same product from two different merchants creates separate MerchantProduct and Offer rows."""
    async with session_factory() as session:
        # Create Merchant A and Source A
        mA = Merchant(
            id=uuid4(), name="Merchant A", merchant_type="brand", verification_status="VERIFIED"
        )
        sA = CatalogSource(
            id=uuid4(),
            merchant_id=mA.id,
            slug=f"source-a-{uuid4().hex[:6]}",
            name="Source A",
            kind="api",
            status="cleared",
            rights_display=True,
            rights_tryon=True,
        )
        # Create Merchant B and Source B
        mB = Merchant(
            id=uuid4(), name="Merchant B", merchant_type="brand", verification_status="VERIFIED"
        )
        sB = CatalogSource(
            id=uuid4(),
            merchant_id=mB.id,
            slug=f"source-b-{uuid4().hex[:6]}",
            name="Source B",
            kind="api",
            status="cleared",
            rights_display=True,
            rights_tryon=True,
        )
        session.add_all([mA, sA, mB, sB])
        await session.commit()
        slugA, slugB = sA.slug, sB.slug
        idA, idB = mA.id, mB.id

    uow = CatalogUnitOfWork(session_factory)
    pipeline = AcquisitionPipeline(uow)

    itemA = SourceProduct(
        source_slug=slugA,
        source_product_id="SHARED-SKU-1",
        title="Classic White Tee",
        category="tops",
        subcategory="tshirt",
        price_minor=99900,
        currency="INR",
        product_url="https://merchantA.com/p1",
    )
    itemB = SourceProduct(
        source_slug=slugB,
        source_product_id="SHARED-SKU-1",
        title="Classic White Tee",
        category="tops",
        subcategory="tshirt",
        price_minor=89900,
        currency="INR",
        product_url="https://merchantB.com/p1",
    )

    await pipeline.process_batch(AcquisitionBatch(source_slug=slugA, products=[itemA]), apply=True)
    await pipeline.process_batch(AcquisitionBatch(source_slug=slugB, products=[itemB]), apply=True)

    async with uow:
        prodA = await uow.merchant_products.get_by_source_id(idA, "SHARED-SKU-1")
        prodB = await uow.merchant_products.get_by_source_id(idB, "SHARED-SKU-1")
        assert prodA is not None and prodB is not None
        assert prodA.merchant_id == idA
        assert prodB.merchant_id == idB
        assert prodA.id != prodB.id

        offerA = await uow.offers.get_by_merchant_and_product(idA, "SHARED-SKU-1")
        offerB = await uow.offers.get_by_merchant_and_product(idB, "SHARED-SKU-1")
        assert offerA.price_minor == 99900
        assert offerB.price_minor == 89900


@pytest.mark.asyncio
async def test_ing_029_worker_retries_same_batch_idempotent(
    session_factory: async_sessionmaker[AsyncSession],
    setup_authorized_source: dict,
) -> None:
    """ING-029: Retrying the exact same batch produces zero new products and zero duplicates."""
    uow = CatalogUnitOfWork(session_factory)
    pipeline = AcquisitionPipeline(uow)
    source_slug = setup_authorized_source["source_slug"]

    item = SourceProduct(
        source_slug=source_slug,
        source_product_id="RETRY-SKU-001",
        title="Formal Black Trousers",
        category="bottoms",
        subcategory="trousers",
        price_minor=249900,
        currency="INR",
        product_url="https://merchant.example.com/p/retry",
    )
    batch = AcquisitionBatch(source_slug=source_slug, products=[item])

    r1 = await pipeline.process_batch(batch, apply=True)
    assert r1.inserted == 1

    r2 = await pipeline.process_batch(batch, apply=True)
    assert r2.inserted == 0
    assert r2.unchanged == 1

    r3 = await pipeline.process_batch(batch, apply=True)
    assert r3.inserted == 0
    assert r3.unchanged == 1
