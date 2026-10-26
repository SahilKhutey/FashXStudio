import hashlib
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from database.models.catalog import (
    CatalogSource,
    Merchant,
)
from fashx.catalog.application.ingest_product import (
    IngestMerchantProductUseCase,
    IngestProductCommand,
)
from fashx.catalog.repositories.catalog_repository import CatalogUnitOfWork
from fashx.core.errors import EntityNotFoundError


@pytest.mark.asyncio
async def test_fallback_source_created_as_unapproved(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """When no source is pre-registered, ingestion fails (no source auto-created). When pre-registered as pending, tryon fails closed."""
    uow = CatalogUnitOfWork(session_factory)
    async with uow:
        merchant = Merchant(name="Unapproved Retailer", merchant_type="retailer")
        uow.merchants.add(merchant)
        await uow.commit()
        merchant_id = merchant.id

    use_case = IngestMerchantProductUseCase(uow)
    cmd = IngestProductCommand(
        merchant_id=merchant_id,
        source_product_id="SKU-UNAPP-1",
        title="Unapproved Top",
        source_url="https://merchant.example.com/items/1",
        category="tops",
        price_minor=129900,
    )
    # Unregistered source must fail
    with pytest.raises(EntityNotFoundError):
        await use_case.execute(cmd)

    # Now register a pending source
    async with uow:
        source = CatalogSource(
            slug=f"merchant-{merchant_id}",
            name=merchant.name,
            kind="manual",
            status="pending",
            rights_display=False,
            rights_tryon=False,
            image_policy="mirror",
        )
        uow.sources.add(source)
        await uow.commit()

    result = await use_case.execute(cmd)
    async with uow:
        garment = await uow.canonical_garments.get_by_id(result.canonical_garment_id)
        assert garment is not None
        assert garment.tryon_supported is False


@pytest.mark.asyncio
async def test_unknown_source_id_raises_not_found(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    uow = CatalogUnitOfWork(session_factory)
    async with uow:
        merchant = Merchant(name="Sample Brand", merchant_type="brand")
        uow.merchants.add(merchant)
        await uow.commit()
        merchant_id = merchant.id

    use_case = IngestMerchantProductUseCase(uow)
    cmd = IngestProductCommand(
        merchant_id=merchant_id,
        source_id=uuid4(),  # unknown random UUID
        source_product_id="SKU-ERR-1",
        title="Sample Top",
        source_url="https://example.com/item",
        category="tops",
        price_minor=99900,
    )
    with pytest.raises(EntityNotFoundError):
        await use_case.execute(cmd)


@pytest.mark.asyncio
async def test_image_persistence_and_deduplication(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    uow = CatalogUnitOfWork(session_factory)
    async with uow:
        merchant = Merchant(name="Studio Merchant", merchant_type="brand")
        source = CatalogSource(
            slug="studio-cleared",
            name="Studio Cleared",
            kind="manual",
            status="cleared",
            rights_display=True,
            rights_tryon=True,
            image_policy="mirror",
        )
        uow.merchants.add(merchant)
        uow.sources.add(source)
        await uow.commit()
        merchant_id = merchant.id
        source_id = source.id

    use_case = IngestMerchantProductUseCase(uow)
    img_url = "https://images.fashx.studio/products/shirt-001.jpg"
    expected_hash = hashlib.sha256(img_url.encode("utf-8")).hexdigest()

    # 1. Ingest with image
    cmd1 = IngestProductCommand(
        merchant_id=merchant_id,
        source_id=source_id,
        source_product_id="P-IMG-001",
        title="Linen Shirt",
        source_url="https://fashx.studio/p001",
        category="tops",
        price_minor=149900,
        image_url=img_url,
        image_rights="owned",
        tryon_rights=True,
    )
    res1 = await use_case.execute(cmd1)
    assert res1.image_id is not None
    assert res1.tryon_supported is True

    # Check GarmentImage record in DB
    async with uow:
        img_record = await uow.images.get_by_hash(expected_hash)
        assert img_record is not None
        assert img_record.garment_id == res1.canonical_garment_id
        assert img_record.storage_key == img_url

    # 2. Ingest update with same image - must be idempotent and reuse image record
    cmd2 = IngestProductCommand(
        merchant_id=merchant_id,
        source_id=source_id,
        source_product_id="P-IMG-001",
        title="Linen Shirt Updated",
        source_url="https://fashx.studio/p001",
        category="tops",
        price_minor=129900,
        image_url=img_url,
        image_rights="owned",
        tryon_rights=True,
    )
    res2 = await use_case.execute(cmd2)
    assert res2.canonical_garment_id == res1.canonical_garment_id
    assert res2.image_id == res1.image_id
    assert res2.price_minor == 129900


@pytest.mark.asyncio
async def test_tryon_rights_enforced_independently_of_display_rights(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    uow = CatalogUnitOfWork(session_factory)
    async with uow:
        merchant = Merchant(name="Display Only Brand", merchant_type="brand")
        # Cleared source with display rights = True, but tryon rights = False
        source = CatalogSource(
            slug="display-only",
            name="Display Only",
            kind="manual",
            status="cleared",
            rights_display=True,
            rights_tryon=False,
            image_policy="mirror",
        )
        uow.merchants.add(merchant)
        uow.sources.add(source)
        await uow.commit()
        merchant_id = merchant.id
        source_id = source.id

    use_case = IngestMerchantProductUseCase(uow)
    cmd = IngestProductCommand(
        merchant_id=merchant_id,
        source_id=source_id,
        source_product_id="P-NOTRYON-1",
        title="Display-Only Trousers",
        source_url="https://example.com/pants",
        category="bottoms",
        price_minor=199900,
        image_url="https://example.com/pants.jpg",
        image_rights="licensed",
        tryon_rights=True,  # Product requests tryon, but source has rights_tryon=False
    )
    res = await use_case.execute(cmd)
    # Must fail closed: tryon_supported must be False
    assert res.tryon_supported is False

    async with uow:
        garment = await uow.canonical_garments.get_by_id(res.canonical_garment_id)
        assert garment is not None
        assert garment.tryon_supported is False
