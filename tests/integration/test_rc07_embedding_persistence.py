from __future__ import annotations

import io
import uuid
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from PIL import Image
from sqlalchemy import event, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from database.models import Base
from database.models.catalog import (
    Brand,
    CanonicalGarment,
    CatalogSource,
    GarmentEnrichment,
    GarmentImage,
)
from fashx.catalog.embeddings.fake import FakeEmbedder
from scripts.catalog.embed_garments import embed_garments


class MockStorage:
    def __init__(self, data_map: dict[str, bytes]) -> None:
        self.data_map = data_map

    def get(self, key: str) -> bytes | None:
        return self.data_map.get(key)


def make_test_jpeg(w: int = 160, h: int = 160) -> bytes:
    img = Image.new("RGB", (w, h), color=(80, 140, 200))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


@pytest_asyncio.fixture
async def session_factory() -> AsyncGenerator[async_sessionmaker[AsyncSession], None]:
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
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
async def test_embed_garments_persistence_flow(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    embedder = FakeEmbedder()
    expected_model_key = f"{embedder.model_id}:{embedder.model_version}"

    test_img_bytes = make_test_jpeg()
    storage_key = "garments/test-brand/item-1/photo.jpg"
    storage = MockStorage({storage_key: test_img_bytes})

    # 1. Seed brand, source, garment, image
    brand_id = uuid.uuid4()
    source_id = uuid.uuid4()
    garment_id = uuid.uuid4()
    image_id = uuid.uuid4()

    async with session_factory() as session:
        brand = Brand(id=brand_id, name="Test Brand", normalized_name="test-brand")
        source = CatalogSource(
            id=source_id,
            slug="test-source",
            name="Test Source",
            kind="test",
            status="cleared",
            rights_display=True,
            rights_tryon=True,
        )
        garment = CanonicalGarment(
            id=garment_id,
            brand_id=brand_id,
            display_name="Linen Summer Kurta",
            gender="men",
            category="tops",
            subcategory="kurta",
            price_minor=4500,
        )
        image = GarmentImage(
            id=image_id,
            garment_id=garment_id,
            storage_key=storage_key,
            content_hash="abc123hash",
            image_type="primary",
        )
        session.add_all([brand, source, garment, image])
        await session.commit()

    # 2. Dry run first: verifies count without persisting
    dry_count = await embed_garments(
        apply=False,
        batch_size=4,
        embedder=embedder,
        session_factory=session_factory,
        storage=storage,
    )
    assert dry_count == 1

    async with session_factory() as session:
        enr_after_dry = (
            await session.execute(
                select(GarmentEnrichment).where(GarmentEnrichment.garment_id == garment_id)
            )
        ).scalar_one_or_none()
        assert enr_after_dry is None

    # 3. Apply embedding: writes vector and versioned model
    applied_count = await embed_garments(
        apply=True,
        batch_size=4,
        embedder=embedder,
        session_factory=session_factory,
        storage=storage,
    )
    assert applied_count == 1

    async with session_factory() as session:
        enr = (
            await session.execute(
                select(GarmentEnrichment).where(GarmentEnrichment.garment_id == garment_id)
            )
        ).scalar_one_or_none()
        assert enr is not None
        assert enr.embedding is not None
        assert len(enr.embedding) == 512
        assert enr.embedding_model == expected_model_key

    # 4. Re-running with same model finds 0 garments needing embedding
    rerun_count = await embed_garments(
        apply=True,
        batch_size=4,
        embedder=embedder,
        session_factory=session_factory,
        storage=storage,
    )
    assert rerun_count == 0
