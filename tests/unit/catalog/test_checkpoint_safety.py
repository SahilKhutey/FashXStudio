"""SA-014, SA-017, SA-018: Checkpoint persistence, crash recovery, and idempotent re-read."""

from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from database.models.catalog import MerchantProduct
from database.models.catalog_sync import CatalogSyncRun
from fashx.catalog.acquisition.checkpoints import SyncCheckpointManager
from fashx.catalog.acquisition.contract import SourceBatch, SourceProduct
from fashx.catalog.acquisition.sync_engine import CatalogSyncEngine


class FlakyPaginationAdapter:
    """Adapter that yields page 1, crashes on page 2, and can resume."""

    def __init__(self, source_slug: str, should_fail_page_2: bool = False) -> None:
        self.source_slug = source_slug
        self.should_fail_page_2 = should_fail_page_2

    async def fetch_page(self, cursor: str | None = None, limit: int = 100) -> SourceBatch:
        if cursor is None:
            products = [
                SourceProduct(
                    source_slug=self.source_slug,
                    source_product_id="prod-page1-item1",
                    title="Page 1 Item 1",
                    brand="BrandA",
                    description="Desc 1",
                    category="dresses",
                    price_minor=2999,
                    currency="INR",
                    in_stock=True,
                    product_url="https://example.com/p1",
                    image_url="https://example.com/p1.jpg",
                )
            ]
            return SourceBatch(
                source_slug=self.source_slug,
                products=products,
                cursor="page_token_2",
                has_more=True,
            )

        if cursor == "page_token_2":
            if self.should_fail_page_2:
                raise RuntimeError("Network timeout on page 2")
            products = [
                SourceProduct(
                    source_slug=self.source_slug,
                    source_product_id="prod-page2-item2",
                    title="Page 2 Item 2",
                    brand="BrandB",
                    description="Desc 2",
                    category="tops",
                    price_minor=1999,
                    currency="INR",
                    in_stock=True,
                    product_url="https://example.com/p2",
                    image_url="https://example.com/p2.jpg",
                )
            ]
            return SourceBatch(
                source_slug=self.source_slug,
                products=products,
                cursor=None,
                has_more=False,
            )

        return SourceBatch(source_slug=self.source_slug, products=[], cursor=None, has_more=False)

    def normalize_product(self, raw_item: dict) -> SourceProduct:
        raise NotImplementedError


@pytest.mark.asyncio
async def test_sa_014_sa_017_checkpoint_advancement_and_crash_safety(
    session_factory: async_sessionmaker[AsyncSession],
    setup_authorized_source: dict,
) -> None:
    """SA-014, SA-017: If sync crashes midway, checkpoint holds last committed page."""
    source_id = setup_authorized_source["source_id"]
    source_slug = setup_authorized_source["source_slug"]
    engine = CatalogSyncEngine(session_factory)

    # 1. First run crashes on page 2
    failing_adapter = FlakyPaginationAdapter(source_slug=source_slug, should_fail_page_2=True)
    with pytest.raises(RuntimeError) as exc_info:
        await engine.execute_sync(source_id=source_id, adapter=failing_adapter)
    assert "Network timeout on page 2" in str(exc_info.value)

    # Verify that products from page 1 were committed
    async with session_factory() as session:
        prods = (
            (
                await session.execute(
                    select(MerchantProduct).where(MerchantProduct.source_id == source_id)
                )
            )
            .scalars()
            .all()
        )
        assert len(prods) == 1
        assert prods[0].source_product_id == "prod-page1-item1"

        # Verify checkpoint is recorded at page_token_2
        cp = await SyncCheckpointManager.load_checkpoint(
            session, source_id=source_id, checkpoint_type="full"
        )
        assert cp is not None
        assert cp.cursor_data == {"cursor": "page_token_2"}

        # Verify run recorded as failed
        run = (
            (
                await session.execute(
                    select(CatalogSyncRun)
                    .where(CatalogSyncRun.source_id == source_id)
                    .order_by(CatalogSyncRun.started_at.desc())
                )
            )
            .scalars()
            .first()
        )
        assert run is not None
        assert run.status == "failed"


@pytest.mark.asyncio
async def test_sa_018_idempotent_resume_and_re_read(
    session_factory: async_sessionmaker[AsyncSession],
    setup_authorized_source: dict,
) -> None:
    """SA-018: Resume from saved checkpoint completes remaining pages idempotently."""
    source_id = setup_authorized_source["source_id"]
    source_slug = setup_authorized_source["source_slug"]
    engine = CatalogSyncEngine(session_factory)

    # Setup pre-existing checkpoint at page_token_2
    async with session_factory() as session:
        await SyncCheckpointManager.save_checkpoint(
            session,
            source_id=source_id,
            checkpoint_type="full",
            cursor_data={"cursor": "page_token_2"},
        )
        await session.commit()

    # Second run succeeds using working adapter
    working_adapter = FlakyPaginationAdapter(source_slug=source_slug, should_fail_page_2=False)
    await engine.execute_sync(source_id=source_id, adapter=working_adapter)

    # Total products should now include page 2 item
    async with session_factory() as session:
        prods = (
            (
                await session.execute(
                    select(MerchantProduct).where(MerchantProduct.source_id == source_id)
                )
            )
            .scalars()
            .all()
        )
        prod_ids = {p.source_product_id for p in prods}
        assert "prod-page2-item2" in prod_ids
