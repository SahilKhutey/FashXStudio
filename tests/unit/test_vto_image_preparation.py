"""Unit tests for Virtual Try-On garment image preparation service."""

from dataclasses import replace
from io import BytesIO
from pathlib import Path

import httpx
import pytest
from PIL import Image
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from database.models.catalog import CatalogSource
from fashx.catalog.acquisition.contract import AcquisitionBatch, SourceProduct
from fashx.catalog.acquisition.pipeline import AcquisitionPipeline
from fashx.catalog.images.preparation import (
    MAX_DOWNLOAD_BYTES,
    GarmentImagePreparer,
    ImagePreparationError,
    ImageRights,
    PreparedGarmentImage,
)
from fashx.catalog.repositories.catalog_repository import CatalogUnitOfWork
from fashx.infrastructure.storage.local import LocalStorage


class MemoryStorage:
    def __init__(self) -> None:
        self.objects: dict[str, tuple[bytes, str]] = {}

    def put(self, key: str, data: bytes, content_type: str = "image/jpeg") -> None:
        self.objects[key] = (data, content_type)

    def get(self, key: str) -> bytes:
        return self.objects[key][0]


class FailingStorage:
    def put(self, key: str, data: bytes, content_type: str = "image/jpeg") -> None:
        raise OSError("Disk quota exceeded or S3 unavailable")


def make_image_bytes(
    fmt: str = "JPEG",
    size: tuple[int, int] = (300, 400),
    color: str = "blue",
) -> bytes:
    buf = BytesIO()
    img = Image.new("RGB", size, color=color)
    img.save(buf, format=fmt)
    return buf.getvalue()


def default_allowed_rights() -> ImageRights:
    return ImageRights(
        source_status="cleared",
        source_rights_display=True,
        source_rights_tryon=True,
        source_image_policy="mirror",
        item_image_rights="partner_authorized",
        item_tryon_rights=True,
    )


@pytest.mark.asyncio
async def test_valid_authorized_image_prepared_and_stored() -> None:
    storage = MemoryStorage()
    preparer = GarmentImagePreparer(
        storage=storage,
        allowed_hosts={"images.partner.com"},
    )
    raw_bytes = make_image_bytes("PNG", (400, 500), "green")
    rights = default_allowed_rights()

    prepared = await preparer.prepare(
        source_slug="snitch",
        source_product_id="SKU-100",
        image_url="https://images.partner.com/products/shirt.png",
        rights=rights,
        raw_image_bytes=raw_bytes,
    )

    assert isinstance(prepared, PreparedGarmentImage)
    assert prepared.tryon_eligible is True
    assert prepared.content_type == "image/jpeg"
    assert prepared.storage_key.startswith("garments/snitch/SKU-100/")
    assert prepared.storage_key.endswith(".jpg")
    assert prepared.content_hash in prepared.storage_key

    # Verify storage contents
    stored_bytes, content_type = storage.objects[prepared.storage_key]
    assert content_type == "image/jpeg"
    assert len(stored_bytes) == prepared.byte_size

    # Verify stored image is readable and normalized
    with Image.open(BytesIO(stored_bytes)) as im:
        assert im.format == "JPEG"
        assert im.mode == "RGB"
        assert im.size == (400, 500)


@pytest.mark.asyncio
async def test_large_image_downscaled_to_max_dimension() -> None:
    storage = MemoryStorage()
    preparer = GarmentImagePreparer(storage=storage)
    raw_bytes = make_image_bytes("JPEG", (2000, 1500), "red")

    prepared = await preparer.prepare(
        source_slug="fabindia",
        source_product_id="SKU-KURTA-1",
        image_url="https://images.fabindia.com/kurta.jpg",
        rights=default_allowed_rights(),
        raw_image_bytes=raw_bytes,
    )

    assert prepared.width == 1024
    assert prepared.height == 768
    stored_bytes = storage.get(prepared.storage_key)
    with Image.open(BytesIO(stored_bytes)) as im:
        assert im.size == (1024, 768)


@pytest.mark.asyncio
async def test_identical_normalized_images_produce_same_hash() -> None:
    storage = MemoryStorage()
    preparer = GarmentImagePreparer(storage=storage)
    raw_bytes = make_image_bytes("JPEG", (300, 300), "navy")

    p1 = await preparer.prepare(
        source_slug="brand-a",
        source_product_id="SKU-1",
        image_url="https://images.brand.com/1.jpg",
        rights=default_allowed_rights(),
        raw_image_bytes=raw_bytes,
    )
    p2 = await preparer.prepare(
        source_slug="brand-a",
        source_product_id="SKU-2",
        image_url="https://images.brand.com/2.jpg",
        rights=default_allowed_rights(),
        raw_image_bytes=raw_bytes,
    )

    assert p1.content_hash == p2.content_hash


@pytest.mark.asyncio
async def test_display_only_rights_stored_but_not_tryon_eligible() -> None:
    storage = MemoryStorage()
    preparer = GarmentImagePreparer(storage=storage)
    raw_bytes = make_image_bytes("JPEG", (200, 200), "black")

    # Source has display rights, but tryon rights are False
    rights = ImageRights(
        source_status="cleared",
        source_rights_display=True,
        source_rights_tryon=False,
        source_image_policy="mirror",
        item_image_rights="partner_authorized",
        item_tryon_rights=False,
    )

    prepared = await preparer.prepare(
        source_slug="partner",
        source_product_id="SKU-DISPLAY",
        image_url="https://images.partner.com/display.jpg",
        rights=rights,
        raw_image_bytes=raw_bytes,
    )

    assert prepared.tryon_eligible is False
    assert prepared.storage_key in storage.objects


@pytest.mark.asyncio
async def test_pending_source_status_rejected() -> None:
    storage = MemoryStorage()
    preparer = GarmentImagePreparer(storage=storage)
    raw_bytes = make_image_bytes("JPEG", (200, 200))

    rights = ImageRights(
        source_status="pending",
        source_rights_display=True,
        source_rights_tryon=True,
        source_image_policy="mirror",
        item_image_rights="partner_authorized",
        item_tryon_rights=True,
    )

    with pytest.raises(ImagePreparationError, match="must be 'cleared'"):
        await preparer.prepare(
            source_slug="pending-src",
            source_product_id="SKU-1",
            image_url="https://images.partner.com/test.jpg",
            rights=rights,
            raw_image_bytes=raw_bytes,
        )


@pytest.mark.asyncio
async def test_unauthorized_item_rights_rejected() -> None:
    storage = MemoryStorage()
    preparer = GarmentImagePreparer(storage=storage)
    raw_bytes = make_image_bytes("JPEG", (200, 200))

    rights = ImageRights(
        source_status="cleared",
        source_rights_display=True,
        source_rights_tryon=True,
        source_image_policy="mirror",
        item_image_rights="unauthorized_crawl",
        item_tryon_rights=True,
    )

    with pytest.raises(ImagePreparationError, match="Source or item rights do not permit"):
        await preparer.prepare(
            source_slug="cleared-src",
            source_product_id="SKU-1",
            image_url="https://images.partner.com/test.jpg",
            rights=rights,
            raw_image_bytes=raw_bytes,
        )


@pytest.mark.asyncio
async def test_http_scheme_rejected() -> None:
    storage = MemoryStorage()
    preparer = GarmentImagePreparer(storage=storage)

    with pytest.raises(ImagePreparationError, match="Image URL scheme must be 'https'"):
        await preparer.prepare(
            source_slug="partner",
            source_product_id="SKU-1",
            image_url="http://insecure.partner.com/shirt.jpg",
            rights=default_allowed_rights(),
            raw_image_bytes=make_image_bytes(),
        )


@pytest.mark.asyncio
async def test_unapproved_host_rejected() -> None:
    storage = MemoryStorage()
    preparer = GarmentImagePreparer(
        storage=storage,
        allowed_hosts={"images.partner.com"},
    )

    with pytest.raises(ImagePreparationError, match="not in approved image host allowlist"):
        await preparer.prepare(
            source_slug="partner",
            source_product_id="SKU-1",
            image_url="https://images.unapproved-domain.com/shirt.jpg",
            rights=default_allowed_rights(),
        )


@pytest.mark.asyncio
async def test_redirect_response_rejected() -> None:
    storage = MemoryStorage()

    def redirect_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(302, headers={"Location": "https://other.com/image.jpg"})

    transport = httpx.MockTransport(redirect_handler)
    async with httpx.AsyncClient(transport=transport) as client:
        preparer = GarmentImagePreparer(
            storage=storage,
            allowed_hosts={"images.partner.com"},
            http_client=client,
        )
        with pytest.raises(ImagePreparationError, match="HTTP redirects prohibited"):
            await preparer.prepare(
                source_slug="partner",
                source_product_id="SKU-1",
                image_url="https://images.partner.com/shirt.jpg",
                rights=default_allowed_rights(),
            )


@pytest.mark.asyncio
async def test_html_response_rejected() -> None:
    storage = MemoryStorage()

    def html_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, headers={"Content-Type": "text/html"}, content=b"<html>404</html>")

    transport = httpx.MockTransport(html_handler)
    async with httpx.AsyncClient(transport=transport) as client:
        preparer = GarmentImagePreparer(
            storage=storage,
            allowed_hosts={"images.partner.com"},
            http_client=client,
        )
        with pytest.raises(ImagePreparationError, match="Unsupported content-type"):
            await preparer.prepare(
                source_slug="partner",
                source_product_id="SKU-1",
                image_url="https://images.partner.com/shirt.jpg",
                rights=default_allowed_rights(),
            )


@pytest.mark.asyncio
async def test_oversized_download_rejected() -> None:
    storage = MemoryStorage()
    oversized_data = b"0" * (MAX_DOWNLOAD_BYTES + 500)

    def oversized_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, headers={"Content-Type": "image/jpeg"}, content=oversized_data)

    transport = httpx.MockTransport(oversized_handler)
    async with httpx.AsyncClient(transport=transport) as client:
        preparer = GarmentImagePreparer(
            storage=storage,
            allowed_hosts={"images.partner.com"},
            http_client=client,
        )
        with pytest.raises(ImagePreparationError, match="Image exceeds max download limit"):
            await preparer.prepare(
                source_slug="partner",
                source_product_id="SKU-1",
                image_url="https://images.partner.com/shirt.jpg",
                rights=default_allowed_rights(),
            )


@pytest.mark.asyncio
async def test_corrupted_image_bytes_rejected() -> None:
    storage = MemoryStorage()
    preparer = GarmentImagePreparer(storage=storage)
    corrupted_data = b"not-a-valid-image-content-bytes"

    with pytest.raises(ImagePreparationError, match="Image byte validation failed"):
        await preparer.prepare(
            source_slug="partner",
            source_product_id="SKU-1",
            image_url="https://images.partner.com/shirt.jpg",
            rights=default_allowed_rights(),
            raw_image_bytes=corrupted_data,
        )


@pytest.mark.asyncio
async def test_storage_failure_fails_closed() -> None:
    failing_storage = FailingStorage()
    preparer = GarmentImagePreparer(storage=failing_storage)
    raw_bytes = make_image_bytes()

    with pytest.raises(ImagePreparationError, match="Failed to store prepared garment image"):
        await preparer.prepare(
            source_slug="partner",
            source_product_id="SKU-1",
            image_url="https://images.partner.com/shirt.jpg",
            rights=default_allowed_rights(),
            raw_image_bytes=raw_bytes,
        )


@pytest.mark.asyncio
async def test_local_storage_integration(tmp_path: Path) -> None:
    local_storage = LocalStorage(root_dir=tmp_path)
    preparer = GarmentImagePreparer(storage=local_storage)
    raw_bytes = make_image_bytes("JPEG", (250, 250), "yellow")

    prepared = await preparer.prepare(
        source_slug="westside",
        source_product_id="WEST-99",
        image_url="https://images.westside.com/west-99.jpg",
        rights=default_allowed_rights(),
        raw_image_bytes=raw_bytes,
    )

    assert local_storage.exists(prepared.storage_key)
    retrieved = local_storage.get(prepared.storage_key)
    assert len(retrieved) == prepared.byte_size


@pytest.mark.asyncio
async def test_pipeline_persists_prepared_image_assets(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    uow = CatalogUnitOfWork(session_factory)
    async with uow:
        source = CatalogSource(
            slug="approved-feed",
            name="Approved Partner",
            kind="feed_url",
            status="cleared",
            rights_display=True,
            rights_tryon=True,
            image_policy="mirror",
        )
        uow.sources.add(source)
        await uow.commit()

    storage = MemoryStorage()
    preparer = GarmentImagePreparer(storage=storage)
    raw_bytes = make_image_bytes("JPEG", (400, 400), "teal")

    item = SourceProduct(
        source_slug="approved-feed",
        source_product_id="SKU-PREPARED-1",
        title="Teal Linen Shirt",
        category="tops",
        price_minor=129900,
        currency="INR",
        product_url="https://approved.example/p/1",
        image_url="https://images.approved.example/p/1.jpg",
        image_rights="partner_authorized",
        tryon_rights=True,
    )

    # 1. Prepare image
    rights = ImageRights(
        source_status=source.status,
        source_rights_display=source.rights_display,
        source_rights_tryon=source.rights_tryon,
        source_image_policy=source.image_policy,
        item_image_rights=item.image_rights,
        item_tryon_rights=item.tryon_rights,
    )
    prepared = await preparer.prepare(
        source_slug=item.source_slug,
        source_product_id=item.source_product_id,
        image_url=item.image_url,
        rights=rights,
        raw_image_bytes=raw_bytes,
    )

    prepared_item = replace(
        item,
        prepared_image_key=prepared.storage_key,
        prepared_image_hash=prepared.content_hash,
    )

    # 2. Ingest through AcquisitionPipeline
    pipeline = AcquisitionPipeline(uow)
    batch = AcquisitionBatch(source_slug="approved-feed", products=[prepared_item])
    report = await pipeline.process_batch(batch, apply=True)
    assert report.success is True
    assert report.inserted == 1

    # 3. Verify GarmentImage was persisted with prepared key and hash (NOT the raw external URL)
    async with uow:
        garment = (await uow.canonical_garments.list(limit=10))[0]
        garment_id = garment.id
        images = await uow.images.list_for_garment(garment_id)
        assert len(images) == 1
        assert images[0].storage_key == prepared.storage_key
        assert images[0].content_hash == prepared.content_hash
        assert images[0].storage_key.startswith("garments/approved-feed/SKU-PREPARED-1/")
        assert images[0].storage_key != item.image_url

    # 4. Update product with new prepared image
    raw_bytes_v2 = make_image_bytes("JPEG", (500, 500), "coral")
    prepared_v2 = await preparer.prepare(
        source_slug=item.source_slug,
        source_product_id=item.source_product_id,
        image_url=item.image_url,
        rights=rights,
        raw_image_bytes=raw_bytes_v2,
    )
    prepared_item_v2 = replace(
        item,
        title="Teal Linen Shirt Updated",
        prepared_image_key=prepared_v2.storage_key,
        prepared_image_hash=prepared_v2.content_hash,
    )
    batch2 = AcquisitionBatch(source_slug="approved-feed", products=[prepared_item_v2])
    report2 = await pipeline.process_batch(batch2, apply=True)
    assert report2.success is True
    assert report2.updated == 1

    # 5. Verify both images are present without duplicate errors
    async with uow:
        images_v2 = await uow.images.list_for_garment(garment_id)
        assert len(images_v2) == 2
        hashes = {img.content_hash for img in images_v2}
        assert prepared.content_hash in hashes
        assert prepared_v2.content_hash in hashes

    # 6. Re-run identical batch - no duplicate image records created
    report3 = await pipeline.process_batch(batch2, apply=True)
    assert report3.success is True
    assert report3.unchanged == 1
    async with uow:
        images_v3 = await uow.images.list_for_garment(garment_id)
        assert len(images_v3) == 2
