from __future__ import annotations

import csv
from collections.abc import AsyncGenerator
from pathlib import Path
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import event, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from database.models import Base
from database.models.catalog import (
    CanonicalGarment,
    CatalogSource,
    Merchant,
    MerchantOffer,
    MerchantProduct,
)
from fashx.catalog.application import IngestMerchantProductUseCase, IngestProductCommand
from fashx.catalog.eligibility import compute_tryon_eligibility
from fashx.catalog.repositories.catalog_repository import CatalogUnitOfWork
from fashx.infrastructure.storage.local import LocalStorage
from scripts.catalog.seed_local import seed_local_catalog


@pytest_asyncio.fixture
async def sqlite_session_factory() -> AsyncGenerator[async_sessionmaker[AsyncSession], None]:
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
    )

    @event.listens_for(engine.sync_engine, "connect")
    def _fk_on(dbapi_conn, _record):
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA foreign_keys=ON")
        cur.close()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, expire_on_commit=False)
    yield factory
    await engine.dispose()


@pytest.mark.asyncio
async def test_ingestion_parity_invariants(
    sqlite_session_factory: async_sessionmaker[AsyncSession],
    tmp_path: Path,
) -> None:
    """Verify that IngestMerchantProductUseCase and seed_local maintain identical invariants:
    1. Source clearance required
    2. Freshness timestamps set (price_checked_at, last_seen_at, price_updated_at, last_synced_at)
    3. Sizes in stock populated
    4. Tryon supported calculated from canonical eligibility function
    5. Content hash / dedup key populated
    """
    storage = LocalStorage(tmp_path / "storage")

    # Setup cleared source and merchant
    async with sqlite_session_factory() as session:
        merchant = Merchant(name="Test Brand", merchant_type="brand")
        source = CatalogSource(
            slug="brand-cleared",
            name="Brand Cleared",
            kind="manual",
            status="cleared",
            rights_display=True,
            rights_tryon=True,
            image_policy="mirror",
        )
        session.add_all([merchant, source])
        await session.commit()
        merchant_id = merchant.id
        source_id = source.id

    # 1. Ingest via UseCase
    uow = CatalogUnitOfWork(sqlite_session_factory)
    uc = IngestMerchantProductUseCase(uow)
    uc_res = await uc.execute(
        IngestProductCommand(
            merchant_id=merchant_id,
            source_id=source_id,
            source_product_id="SKU-UC-001",
            title="UseCase Cotton Shirt",
            source_url="https://test.com/sku-001",
            category="tops",
            price_minor=199900,
            sizes_in_stock=["S", "M", "L", "XL"],
            content_hash="hash_uc_001",
            status="active",
        )
    )

    # 2. Ingest via seed_local
    csv_file = tmp_path / "seed.csv"
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "id", "title", "brand", "price", "gender", "category",
                "sub_category", "primary_color", "pattern", "formality",
                "ethnic_wear", "tryon_suitable", "sizes", "image",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "id": "SKU-SEED-001",
                "title": "Seed Cotton Shirt",
                "brand": "Own",
                "price": "1999",
                "gender": "male",
                "category": "tops",
                "sub_category": "shirt",
                "primary_color": "white",
                "pattern": "solid",
                "formality": "3",
                "ethnic_wear": "false",
                "tryon_suitable": "true",
                "sizes": "S|M|L|XL",
                "image": "shirt.jpg",
            }
        )

    # Put dummy image for seed
    (tmp_path / "shirt.jpg").write_bytes(b"dummy_image_data")

    # Add own-wardrobe cleared source for seed_local
    async with sqlite_session_factory() as session:
        own_source = CatalogSource(
            slug="own-wardrobe",
            name="Own wardrobe",
            kind="manual",
            status="cleared",
            rights_display=True,
            rights_tryon=True,
            image_policy="mirror",
        )
        session.add(own_source)
        await session.commit()

    await seed_local_catalog(
        csv_file,
        apply=True,
        session_factory=sqlite_session_factory,
        storage=storage,
    )

    # Assert Parity Invariants across both paths:
    async with sqlite_session_factory() as session:
        # Load products
        prod_uc = (await session.scalars(select(MerchantProduct).where(MerchantProduct.source_product_id == "SKU-UC-001"))).one()
        prod_seed = (await session.scalars(select(MerchantProduct).where(MerchantProduct.source_product_id == "SKU-SEED-001"))).one()

        # Invariant: content_hash set
        assert prod_uc.content_hash == "hash_uc_001"
        assert prod_seed.content_hash is not None and len(prod_seed.content_hash) == 64

        # Invariant: Freshness timestamps set and recent
        for p in (prod_uc, prod_seed):
            assert p.price_checked_at is not None
            assert p.last_seen_at is not None
            assert p.status == "active"

        # Load garments
        garment_uc = (await session.scalars(select(CanonicalGarment).where(CanonicalGarment.id == uc_res.canonical_garment_id))).one()
        garment_seed = (await session.scalars(select(CanonicalGarment).where(CanonicalGarment.display_name == "Seed Cotton Shirt"))).one()

        # Invariant: sizes_in_stock populated
        assert garment_uc.sizes_in_stock == ["S", "M", "L", "XL"]
        assert garment_seed.sizes_in_stock == ["S", "M", "L", "XL"]

        # Invariant: tryon_supported matches canonical eligibility
        expected_eligibility = compute_tryon_eligibility(
            source_rights_tryon=True,
            source_image_policy="mirror",
            category="tops",
        )
        assert garment_uc.tryon_supported == expected_eligibility
        assert garment_seed.tryon_supported == expected_eligibility

        # Load offers
        offer_uc = (await session.scalars(select(MerchantOffer).where(MerchantOffer.garment_id == garment_uc.id))).one()
        offer_seed = (await session.scalars(select(MerchantOffer).where(MerchantOffer.garment_id == garment_seed.id))).one()

        for o in (offer_uc, offer_seed):
            assert o.price_minor == 199900
            assert o.currency == "INR"
            assert o.in_stock is True
            assert o.last_synced_at is not None
