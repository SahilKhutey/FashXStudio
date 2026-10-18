from __future__ import annotations

import csv
from collections.abc import AsyncGenerator
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy import event, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from database.models import Base
from database.models.catalog import (
    CanonicalGarment,
    CatalogSource,
    GarmentEnrichment,
    GarmentImage,
    MerchantOffer,
    MerchantProduct,
)
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


@pytest.fixture
def catalog_fixture(tmp_path: Path) -> Path:
    img_dir = tmp_path / "images"
    img_dir.mkdir(parents=True)

    img1 = img_dir / "g001.jpg"
    img1.write_bytes(b"dummy_image_1_kurta_bytes")
    img2 = img_dir / "g002.jpg"
    img2.write_bytes(b"dummy_image_2_pants_bytes")

    csv_path = tmp_path / "catalog.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "id",
                "title",
                "brand",
                "price",
                "gender",
                "category",
                "sub_category",
                "primary_color",
                "pattern",
                "formality",
                "ethnic_wear",
                "tryon_suitable",
                "sizes",
                "image",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "id": "g001",
                "title": "Teal Cotton Kurta",
                "brand": "Own",
                "price": "1299",
                "gender": "female",
                "category": "tops",
                "sub_category": "kurta",
                "primary_color": "teal",
                "pattern": "solid",
                "formality": "3",
                "ethnic_wear": "true",
                "tryon_suitable": "true",
                "sizes": "S|M|L",
                "image": "images/g001.jpg",
            }
        )
        writer.writerow(
            {
                "id": "g002",
                "title": "Slim Blue Trousers",
                "brand": "Own",
                "price": "1999",
                "gender": "unisex",
                "category": "bottoms",
                "sub_category": "trousers",
                "primary_color": "blue",
                "pattern": "solid",
                "formality": "2",
                "ethnic_wear": "false",
                "tryon_suitable": "false",
                "sizes": "30|32",
                "image": "images/g002.jpg",
            }
        )
    return csv_path


@pytest.mark.asyncio
async def test_seed_local_catalog_dry_run_apply_and_idempotency(
    sqlite_session_factory: async_sessionmaker[AsyncSession],
    catalog_fixture: Path,
    tmp_path: Path,
) -> None:
    storage = LocalStorage(tmp_path / "media")

    # 1. Setup: add cleared own-wardrobe source
    async with sqlite_session_factory() as session:
        source = CatalogSource(
            slug="own-wardrobe",
            name="Own Wardrobe",
            kind="manual",
            status="cleared",
            rights_display=True,
            rights_tryon=True,
            image_policy="mirror",
        )
        session.add(source)
        await session.commit()

    # Step 1: DRY RUN writes nothing to DB or storage
    await seed_local_catalog(
        catalog_fixture,
        apply=False,
        session_factory=sqlite_session_factory,
        storage=storage,
    )

    async with sqlite_session_factory() as session:
        products = (await session.scalars(select(MerchantProduct))).all()
        garments = (await session.scalars(select(CanonicalGarment))).all()
        assert len(products) == 0
        assert len(garments) == 0

    # Step 2: APPLY creates the expected products, canonical garments, offers, images and enrichments
    await seed_local_catalog(
        catalog_fixture,
        apply=True,
        session_factory=sqlite_session_factory,
        storage=storage,
    )

    async with sqlite_session_factory() as session:
        products = (await session.scalars(select(MerchantProduct))).all()
        garments = (await session.scalars(select(CanonicalGarment).order_by(CanonicalGarment.display_name))).all()
        offers = (await session.scalars(select(MerchantOffer))).all()
        images = (await session.scalars(select(GarmentImage))).all()
        enrichments = (await session.scalars(select(GarmentEnrichment))).all()

        assert len(products) == 2
        assert len(garments) == 2
        assert len(offers) == 2
        assert len(images) == 2
        assert len(enrichments) == 2

        # Check freshness timestamps
        for p in products:
            assert p.last_seen_at is not None
            assert p.price_checked_at is not None
        for o in offers:
            assert o.last_synced_at is not None
        for g in garments:
            assert g.price_updated_at is not None

        # Check g002: tryon_suitable was false, so tryon_supported must be False
        trousers = next(g for g in garments if "Trousers" in g.display_name)
        assert trousers.tryon_supported is False

        # Check g001: category=tops, tryon_suitable=true, cleared mirror source -> tryon_supported is True
        kurta = next(g for g in garments if "Kurta" in g.display_name)
        assert kurta.tryon_supported is True
        assert kurta.price_minor == 129900
        assert kurta.sizes_in_stock == ["S", "M", "L"]

        # Check enrichment source of truth
        for enr in enrichments:
            assert enr.attributes_json["source_of_truth"] == "human"
            assert enr.confidence_summary["overall"] == 1.0

        # Check storage has the files
        for img in images:
            assert storage.exists(img.storage_key) is True

    # Step 3: Second APPLY is idempotent (zero extra garments or offers)
    await seed_local_catalog(
        catalog_fixture,
        apply=True,
        session_factory=sqlite_session_factory,
        storage=storage,
    )

    async with sqlite_session_factory() as session:
        products_after = (await session.scalars(select(MerchantProduct))).all()
        garments_after = (await session.scalars(select(CanonicalGarment))).all()
        offers_after = (await session.scalars(select(MerchantOffer))).all()

        assert len(products_after) == 2
        assert len(garments_after) == 2
        assert len(offers_after) == 2


@pytest.mark.asyncio
async def test_seed_refreshes_price_freshness_after_time_advancement(
    catalog_fixture: Path,
    sqlite_session_factory: async_sessionmaker[AsyncSession],
    tmp_path: Path,
) -> None:
    from datetime import datetime, timedelta, timezone
    from scripts.catalog.embed_garments import embed_garments
    from fashx.catalog.embeddings.fake import FakeEmbedder

    storage = LocalStorage(tmp_path / "storage")

    # Add cleared own-wardrobe source
    async with sqlite_session_factory() as session:
        source = CatalogSource(
            slug="own-wardrobe",
            name="Own Wardrobe",
            kind="manual",
            status="cleared",
            rights_display=True,
            rights_tryon=True,
            image_policy="mirror",
        )
        session.add(source)
        await session.commit()

    # Initial seed
    await seed_local_catalog(
        catalog_fixture,
        apply=True,
        session_factory=sqlite_session_factory,
        storage=storage,
    )

    # Simulate advancing clock by 80 hours: manually backdate price_checked_at
    past_time = datetime.now(timezone.utc) - timedelta(hours=80)
    async with sqlite_session_factory() as session:
        products = (await session.scalars(select(MerchantProduct))).all()
        for p in products:
            p.price_checked_at = past_time
            p.last_seen_at = past_time
        await session.commit()

    def to_utc(dt: datetime) -> datetime:
        return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)

    # Verify that products are now stale (> 72 hours)
    async with sqlite_session_factory() as session:
        stale_products = (await session.scalars(select(MerchantProduct))).all()
        for p in stale_products:
            age_hours = (datetime.now(timezone.utc) - to_utc(p.price_checked_at)).total_seconds() / 3600.0
            assert age_hours >= 79.0

    # Re-run seed with --apply
    await seed_local_catalog(
        catalog_fixture,
        apply=True,
        session_factory=sqlite_session_factory,
        storage=storage,
    )

    # Verify that price_checked_at and last_seen_at were refreshed to current time
    async with sqlite_session_factory() as session:
        refreshed_products = (await session.scalars(select(MerchantProduct))).all()
        for p in refreshed_products:
            age_hours = (datetime.now(timezone.utc) - to_utc(p.price_checked_at)).total_seconds() / 3600.0
            assert age_hours < 0.1  # freshly updated within seconds
            assert p.status == "active"

    # Test embed_garments with FakeEmbedder
    embedded_count = await embed_garments(
        apply=True,
        batch_size=8,
        use_fake=True,
        session_factory=sqlite_session_factory,
        storage=storage,
    )
    assert embedded_count == 2

    async with sqlite_session_factory() as session:
        enrichments = (await session.scalars(select(GarmentEnrichment))).all()
        for enr in enrichments:
            assert enr.embedding_model == "mock-fake-512"
            assert enr.embedding is not None
            assert len(enr.embedding) == 512

