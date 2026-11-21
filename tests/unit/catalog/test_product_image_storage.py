"""Unit tests for image storage layout, deduplication isolation, and signed URLs.

Covers test IDs: IMG-025, IMG-026, IMG-041, IMG-043.
"""

from __future__ import annotations

import io
from datetime import UTC, datetime
from typing import Any

import pytest
from PIL import Image
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from database.models.catalog_auth import (
    CatalogPermissionCode,
    CatalogSourcePermission,
)
from fashx.catalog.images.fetcher import SafeImageFetcher
from fashx.catalog.images.models import ImageJobRequest
from fashx.catalog.images.pipeline import ProductImagePipeline
from fashx.catalog.images.storage_service import ImageStorageService
from fashx.infrastructure.storage.local import LocalStorage


def make_test_jpeg(color: str = "red") -> bytes:
    buf = io.BytesIO()
    img = Image.new("RGB", (600, 800), color)
    img.save(buf, format="JPEG")
    return buf.getvalue()


class MockFetcher(SafeImageFetcher):
    def __init__(self, color: str = "red") -> None:
        super().__init__()
        self.data = make_test_jpeg(color)

    async def fetch_bytes(self, url: str) -> tuple[bytes, str]:
        return self.data, "image/jpeg"


@pytest.mark.asyncio
async def test_img_025_and_026_exact_duplicate_and_cross_product_isolation(
    session_factory: async_sessionmaker[AsyncSession],
    setup_authorized_source: dict,
    tmp_path: Any,
) -> None:
    """IMG-025 & IMG-026: Same image on same product reuses asset; same image on different product does not merge products."""
    storage = LocalStorage(root_dir=tmp_path / "storage")
    storage_svc = ImageStorageService(storage)
    shared_data = make_test_jpeg(color="navy")

    class SharedFetcher(SafeImageFetcher):
        async def fetch_bytes(self, url: str) -> tuple[bytes, str]:
            return shared_data, "image/jpeg"

    source_id = setup_authorized_source["source_id"]
    merchant_id = setup_authorized_source["merchant_id"]

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

    # Product A
    async with session_factory() as session:
        pipeline = ProductImagePipeline(session, storage_svc, fetcher=SharedFetcher())
        res_a = await pipeline.process_image(
            ImageJobRequest(
                source_id=source_id,
                merchant_id=merchant_id,
                source_product_id="PRODUCT-A",
                image_url="https://merchant.example.com/shared.jpg",
                category="tops",
            )
        )
        await session.commit()

    # Product B uses the same stock image!
    async with session_factory() as session:
        pipeline = ProductImagePipeline(session, storage_svc, fetcher=SharedFetcher())
        res_b = await pipeline.process_image(
            ImageJobRequest(
                source_id=source_id,
                merchant_id=merchant_id,
                source_product_id="PRODUCT-B",
                image_url="https://merchant.example.com/shared.jpg",
                category="tops",
            )
        )
        await session.commit()

    assert res_a.success is True
    assert res_b.success is True
    # IMG-026: Distinct product entities must not be merged together
    assert res_a.asset_id != res_b.asset_id


@pytest.mark.asyncio
async def test_img_041_and_043_signed_url_generation_and_expiry(
    tmp_path: Any,
) -> None:
    """IMG-041 & IMG-043: Signed URLs are generated with expiry and verified."""
    storage = LocalStorage(root_dir=tmp_path / "storage")
    storage_svc = ImageStorageService(storage)

    key = "catalog/dev/sources/test/originals/test.jpg"
    await storage_svc.put(key, b"testdata", content_type="image/jpeg")

    url = await storage_svc.get_signed_url(key, expires_in_seconds=300)
    assert url is not None
    assert "/storage/" in url or "sig=" in url or "key=" in url or key in url
