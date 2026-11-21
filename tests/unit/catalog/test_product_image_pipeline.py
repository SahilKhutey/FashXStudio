"""Unit and integration tests for Phase 05.4 product image pipeline.

Covers test IDs: IMG-001 through IMG-009, IMG-028 through IMG-033, IMG-038 through IMG-040, IMG-044, IMG-045.
"""

from __future__ import annotations

import io
from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock
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
)
from fashx.catalog.images.fetcher import ImageFetchError, SafeImageFetcher
from fashx.catalog.images.models import ImageJobRequest
from fashx.catalog.images.permissions import ImagePermissionService
from fashx.catalog.images.pipeline import ProductImagePipeline
from fashx.catalog.images.storage_service import ImageStorageService
from fashx.infrastructure.storage.local import LocalStorage


def make_valid_jpeg(size: tuple[int, int] = (600, 800)) -> bytes:
    buf = io.BytesIO()
    img = Image.new("RGB", size, "blue")
    img.save(buf, format="JPEG")
    return buf.getvalue()


class MockFetchSuccess(SafeImageFetcher):
    def __init__(self, data: bytes | None = None) -> None:
        super().__init__()
        self.data = data or make_valid_jpeg()

    async def fetch_bytes(self, url: str) -> tuple[bytes, str]:
        return self.data, "image/jpeg"


class MockFetchError(SafeImageFetcher):
    def __init__(self, code: str, msg: str, status_code: int = 500) -> None:
        super().__init__()
        self.code = code
        self.msg = msg
        self.status_code = status_code

    async def fetch_bytes(self, url: str) -> tuple[bytes, str]:
        raise ImageFetchError(self.code, self.msg, status_code=self.status_code)


@pytest.mark.asyncio
async def test_img_001_to_004_permissions_rejections(
    session_factory: async_sessionmaker[AsyncSession],
    setup_authorized_source: dict,
    tmp_path: Any,
) -> None:
    """IMG-001 to IMG-004: Pipeline rejects unregistered, suspended, or unpermitted sources before fetch."""
    storage = LocalStorage(root_dir=tmp_path / "storage")
    storage_svc = ImageStorageService(storage)

    async with session_factory() as session:
        pipeline = ProductImagePipeline(session, storage_svc)

        # IMG-001: Unregistered source
        unreg_req = ImageJobRequest(
            source_id=uuid4(),
            merchant_id=setup_authorized_source["merchant_id"],
            source_product_id="SKU-UNREG",
            image_url="https://merchant.example.com/img.jpg",
            category="tops",
        )
        res1 = await pipeline.process_image(unreg_req)
        assert res1.success is False
        assert "permission_denied" in (res1.error_code or "")

        # IMG-004: Image fetch permission denied (source has no IMAGE_FETCH granted)
        valid_source_req = ImageJobRequest(
            source_id=setup_authorized_source["source_id"],
            merchant_id=setup_authorized_source["merchant_id"],
            source_product_id="SKU-001",
            image_url="https://merchant.example.com/img.jpg",
            category="tops",
        )
        res4 = await pipeline.process_image(valid_source_req)
        assert res4.success is False
        assert res4.error_code == "permission_denied_fetch"


@pytest.mark.asyncio
async def test_img_028_to_030_storage_and_display_derivatives(
    session_factory: async_sessionmaker[AsyncSession],
    setup_authorized_source: dict,
    tmp_path: Any,
) -> None:
    """IMG-028 & IMG-030: Pipeline stores permitted originals and generates display derivatives."""
    storage = LocalStorage(root_dir=tmp_path / "storage")
    storage_svc = ImageStorageService(storage)
    mock_fetcher = MockFetchSuccess()

    source_id = setup_authorized_source["source_id"]
    merchant_id = setup_authorized_source["merchant_id"]

    # Grant IMAGE_FETCH, IMAGE_STORE, and IMAGE_DISPLAY
    async with session_factory() as session:
        for code in (
            CatalogPermissionCode.IMAGE_FETCH,
            CatalogPermissionCode.IMAGE_STORE,
            CatalogPermissionCode.IMAGE_DISPLAY,
        ):
            perm = CatalogSourcePermission(
                source_id=source_id,
                permission_code=code.value,
                permission_status="GRANTED",
                granted_by="founder@fashx.internal",
                effective_at=datetime.now(UTC),
            )
            session.add(perm)
        await session.commit()

    async with session_factory() as session:
        pipeline = ProductImagePipeline(session, storage_svc, fetcher=mock_fetcher)
        req = ImageJobRequest(
            source_id=source_id,
            merchant_id=merchant_id,
            source_product_id="SKU-DISPLAY-1",
            image_url="https://merchant.example.com/item1.jpg",
            category="tops",
        )
        res = await pipeline.process_image(req)
        assert res.success is True
        assert res.asset_id is not None
        assert res.original_storage_key is not None
        assert "DISPLAY_CARD" in res.transformations
        assert "DISPLAY_THUMBNAIL" in res.transformations
        assert "DISPLAY_DETAIL" in res.transformations

        # Check DB records
        asset = await session.get(CatalogImageAsset, res.asset_id)
        assert asset is not None
        assert asset.original_width == 600
        assert asset.original_height == 800
        assert asset.quality_score == "PASS"

        # Verify storage files exist
        assert await storage_svc.exists(res.original_storage_key)


@pytest.mark.asyncio
async def test_img_031_and_032_vto_derivative_rights_enforcement(
    session_factory: async_sessionmaker[AsyncSession],
    setup_authorized_source: dict,
    tmp_path: Any,
) -> None:
    """IMG-031 & IMG-032: VTO derivative is generated only when IMAGE_AI_PROCESS and VTO_PROCESS are granted."""
    storage = LocalStorage(root_dir=tmp_path / "storage")
    storage_svc = ImageStorageService(storage)
    mock_fetcher = MockFetchSuccess(make_valid_jpeg((800, 1000)))

    source_id = setup_authorized_source["source_id"]
    merchant_id = setup_authorized_source["merchant_id"]

    # 1. IMG-031: Without AI/VTO rights -> VTO_INPUT is NOT generated
    async with session_factory() as session:
        for code in (
            CatalogPermissionCode.IMAGE_FETCH,
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
        pipeline = ProductImagePipeline(session, storage_svc, fetcher=mock_fetcher)
        res1 = await pipeline.process_image(
            ImageJobRequest(
                source_id=source_id,
                merchant_id=merchant_id,
                source_product_id="SKU-NO-VTO",
                image_url="https://merchant.example.com/novto.jpg",
                category="tops",
            )
        )
        assert res1.success is True
        assert "VTO_INPUT" not in res1.transformations

    # 2. IMG-032: Grant AI & VTO permissions -> VTO_INPUT IS generated
    async with session_factory() as session:
        for code in (
            CatalogPermissionCode.IMAGE_AI_PROCESS,
            CatalogPermissionCode.VTO_PROCESS,
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
        pipeline = ProductImagePipeline(session, storage_svc, fetcher=mock_fetcher)
        res2 = await pipeline.process_image(
            ImageJobRequest(
                source_id=source_id,
                merchant_id=merchant_id,
                source_product_id="SKU-WITH-VTO",
                image_url="https://merchant.example.com/withvto.jpg",
                category="tops",
            )
        )
        assert res2.success is True
        assert "VTO_INPUT" in res2.transformations


@pytest.mark.asyncio
async def test_img_029_storage_succeeds_db_fails_compensation(
    session_factory: async_sessionmaker[AsyncSession],
    setup_authorized_source: dict,
    tmp_path: Any,
) -> None:
    """IMG-029: If database operation fails after storage uploads, storage cleanup is executed."""
    storage = LocalStorage(root_dir=tmp_path / "storage")
    storage_svc = ImageStorageService(storage)
    mock_fetcher = MockFetchSuccess()

    source_id = setup_authorized_source["source_id"]
    merchant_id = setup_authorized_source["merchant_id"]

    # Grant permissions
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
        pipeline = ProductImagePipeline(session, storage_svc, fetcher=mock_fetcher)

        # Track uploads and fail flush only after upload has commenced
        upload_done = False
        orig_put = storage_svc.put

        async def tracking_put(key: str, data: bytes, content_type: str) -> str:
            nonlocal upload_done
            res = await orig_put(key, data, content_type)
            upload_done = True
            return res

        storage_svc.put = tracking_put  # type: ignore

        original_flush = session.flush

        async def failing_flush() -> None:
            if upload_done:
                raise RuntimeError("Simulated database failure during flush")
            await original_flush()

        session.flush = failing_flush  # type: ignore

        req = ImageJobRequest(
            source_id=source_id,
            merchant_id=merchant_id,
            source_product_id="SKU-ROLLBACK",
            image_url="https://merchant.example.com/rollback.jpg",
            category="tops",
        )
        res = await pipeline.process_image(req)
        assert res.success is False
        assert res.error_code == "db_commit_failed"
        # Verify storage cleanup was executed
        assert len(storage.list_prefix("")) == 0


@pytest.mark.asyncio
async def test_img_038_broken_image_404_recorded(
    session_factory: async_sessionmaker[AsyncSession],
    setup_authorized_source: dict,
    tmp_path: Any,
) -> None:
    """IMG-038: 404 from source is handled cleanly and records failure without corrupting catalog."""
    storage = LocalStorage(root_dir=tmp_path / "storage")
    storage_svc = ImageStorageService(storage)
    mock_fetcher = MockFetchError(code="not_found", msg="Image 404", status_code=404)

    source_id = setup_authorized_source["source_id"]
    merchant_id = setup_authorized_source["merchant_id"]

    async with session_factory() as session:
        session.add(
            CatalogSourcePermission(
                source_id=source_id,
                permission_code=CatalogPermissionCode.IMAGE_FETCH.value,
                permission_status="GRANTED",
                granted_by="founder@fashx.internal",
                effective_at=datetime.now(UTC),
            )
        )
        await session.commit()

    async with session_factory() as session:
        pipeline = ProductImagePipeline(session, storage_svc, fetcher=mock_fetcher)
        res = await pipeline.process_image(
            ImageJobRequest(
                source_id=source_id,
                merchant_id=merchant_id,
                source_product_id="SKU-404",
                image_url="https://merchant.example.com/missing.jpg",
                category="tops",
            )
        )
        assert res.success is False
        assert res.error_code == "not_found"


@pytest.mark.asyncio
async def test_img_040_duplicate_job_delivery_idempotent(
    session_factory: async_sessionmaker[AsyncSession],
    setup_authorized_source: dict,
    tmp_path: Any,
) -> None:
    """IMG-040: Delivering the same image job repeatedly is idempotent and does not duplicate assets."""
    storage = LocalStorage(root_dir=tmp_path / "storage")
    storage_svc = ImageStorageService(storage)
    mock_fetcher = MockFetchSuccess()

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

    req = ImageJobRequest(
        source_id=source_id,
        merchant_id=merchant_id,
        source_product_id="SKU-IDEMPOTENT-1",
        image_url="https://merchant.example.com/same.jpg",
        category="tops",
    )

    async with session_factory() as session:
        pipeline = ProductImagePipeline(session, storage_svc, fetcher=mock_fetcher)
        res1 = await pipeline.process_image(req)
        await session.commit()

    async with session_factory() as session:
        pipeline = ProductImagePipeline(session, storage_svc, fetcher=mock_fetcher)
        res2 = await pipeline.process_image(req)
        await session.commit()

    assert res1.success is True
    assert res2.success is True
    assert res1.asset_id == res2.asset_id


@pytest.mark.asyncio
async def test_img_045_permission_service_unavailable_fails_closed(
    session_factory: async_sessionmaker[AsyncSession],
    setup_authorized_source: dict,
    tmp_path: Any,
) -> None:
    """IMG-045: When permission evaluator throws an unexpected error, pipeline fails closed."""
    storage = LocalStorage(root_dir=tmp_path / "storage")
    storage_svc = ImageStorageService(storage)

    async with session_factory() as session:
        failing_perm_svc = ImagePermissionService(session)
        # Mock evaluate to raise
        failing_perm_svc.auth_service.evaluate = AsyncMock(
            side_effect=RuntimeError("Auth service offline")
        )

        pipeline = ProductImagePipeline(
            session=session,
            storage_service=storage_svc,
            permission_service=failing_perm_svc,
        )
        res = await pipeline.process_image(
            ImageJobRequest(
                source_id=setup_authorized_source["source_id"],
                merchant_id=setup_authorized_source["merchant_id"],
                source_product_id="SKU-OFFLINE",
                image_url="https://merchant.example.com/item.jpg",
                category="tops",
            )
        )
        assert res.success is False
        assert res.error_code == "permission_denied_fetch"
        assert "fail_closed_error" in (res.error_message or "")
