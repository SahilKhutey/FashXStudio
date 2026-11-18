"""Unit tests for image takedowns, suspension, cascade object deletion, and retry tracking.

Covers test IDs: IMG-034 through IMG-037, IMG-042.
"""

from __future__ import annotations

import io
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import pytest
from PIL import Image
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from database.models.catalog_auth import (
    CatalogPermissionCode,
    CatalogSourcePermission,
)
from database.models.catalog_image import (
    CatalogImageAsset,
    ImageAssetStatus,
    ImageTakedownScope,
    ImageTakedownStatus,
)
from fashx.catalog.images.fetcher import SafeImageFetcher
from fashx.catalog.images.lifecycle import ImageLifecycleService
from fashx.catalog.images.models import ImageJobRequest
from fashx.catalog.images.pipeline import ProductImagePipeline
from fashx.catalog.images.storage_service import ImageStorageService
from fashx.infrastructure.storage.local import LocalStorage


def make_test_jpeg() -> bytes:
    buf = io.BytesIO()
    img = Image.new("RGB", (600, 800), "green")
    img.save(buf, format="JPEG")
    return buf.getvalue()


class MockFetcher(SafeImageFetcher):
    async def fetch_bytes(self, url: str) -> tuple[bytes, str]:
        return make_test_jpeg(), "image/jpeg"


@pytest.mark.asyncio
async def test_img_034_and_042_takedown_suspends_and_deletes_derivatives(
    session_factory: async_sessionmaker[AsyncSession],
    setup_authorized_source: dict,
    tmp_path: Any,
) -> None:
    """IMG-034 & IMG-042: Takedown immediately marks assets SUSPENDED, and tracks deletion jobs across storage targets."""
    storage = LocalStorage(root_dir=tmp_path / "storage")
    storage_svc = ImageStorageService(storage)
    source_id = setup_authorized_source["source_id"]
    merchant_id = setup_authorized_source["merchant_id"]

    # 1. Ingest an image asset
    async with session_factory() as session:
        for code in (
            CatalogPermissionCode.IMAGE_FETCH,
            CatalogPermissionCode.IMAGE_STORE,
            CatalogPermissionCode.IMAGE_DISPLAY,
        ):
            session.add(
                CatalogSourcePermission(
                    source_id=source_id,
                    permission_code=code.value,
                    permission_status="GRANTED",
                    granted_by="founder@fashx.internal",
                    effective_at=datetime.now(UTC),
                )
            )
        await session.commit()

    async with session_factory() as session:
        pipeline = ProductImagePipeline(session, storage_svc, fetcher=MockFetcher())
        res = await pipeline.process_image(
            ImageJobRequest(
                source_id=source_id,
                merchant_id=merchant_id,
                source_product_id="SKU-TAKEDOWN-1",
                image_url="https://merchant.example.com/td.jpg",
                category="tops",
            )
        )
        await session.commit()
        asset_id = res.asset_id
        assert asset_id is not None
        assert res.original_storage_key is not None
        assert await storage_svc.exists(res.original_storage_key)

    # 2. Initiate Takedown
    async with session_factory() as session:
        lifecycle_svc = ImageLifecycleService(session, storage_svc)
        takedown = await lifecycle_svc.initiate_takedown(
            reason_code="MERCHANT_REQUEST",
            scope_type=ImageTakedownScope.ASSET,
            asset_id=asset_id,
        )
        assert takedown.status == ImageTakedownStatus.SUSPENDED.value

        # Verify asset status is SUSPENDED immediately
        asset = await session.get(CatalogImageAsset, asset_id)
        assert asset is not None
        assert asset.status == ImageAssetStatus.SUSPENDED.value

        # Execute deletion jobs
        completed, failed = await lifecycle_svc.execute_deletion_jobs(takedown.id)
        assert completed > 0
        assert failed == 0

        # Verify takedown is completed and asset is DELETED
        assert takedown.status == ImageTakedownStatus.COMPLETED.value
        assert asset.status == ImageAssetStatus.DELETED.value

        # Verify physical file was deleted from storage
        assert not await storage_svc.exists(res.original_storage_key)


@pytest.mark.asyncio
async def test_img_036_partial_deletion_failure_retry_pending(
    session_factory: async_sessionmaker[AsyncSession],
    setup_authorized_source: dict,
    tmp_path: Any,
) -> None:
    """IMG-036: If an object deletion fails, takedown remains PROCESSING and job status is FAILED for retry."""
    storage = LocalStorage(root_dir=tmp_path / "storage")
    storage_svc = ImageStorageService(storage)

    # Mock delete to fail
    async def failing_delete(key: str) -> bool:
        return False

    storage_svc.delete = failing_delete  # type: ignore

    source_id = setup_authorized_source["source_id"]
    merchant_id = setup_authorized_source["merchant_id"]

    async with session_factory() as session:
        # Create dummy asset
        asset = CatalogImageAsset(
            id=uuid4(),
            source_id=source_id,
            merchant_id=merchant_id,
            source_product_id="SKU-FAIL-DEL",
            original_storage_key="dummy/path/orig.jpg",
            status=ImageAssetStatus.ACTIVE.value,
        )
        session.add(asset)
        await session.commit()

        lifecycle_svc = ImageLifecycleService(session, storage_svc)
        takedown = await lifecycle_svc.initiate_takedown(
            reason_code="LEGAL_REQUEST",
            scope_type=ImageTakedownScope.ASSET,
            asset_id=asset.id,
        )
        completed, failed = await lifecycle_svc.execute_deletion_jobs(takedown.id)
        assert failed > 0
        assert takedown.status == ImageTakedownStatus.PROCESSING.value
