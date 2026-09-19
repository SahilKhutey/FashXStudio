import io
from uuid import uuid4

import pytest
from api.app.catalog.application.enrich_garment import (
    EnrichGarmentCommand,
    EnrichGarmentUseCase,
)
from api.app.catalog.application.ingest_product import (
    IngestMerchantProductUseCase,
    IngestProductCommand,
)
from api.app.catalog.repositories.catalog_repository import CatalogUnitOfWork
from api.app.core.errors import ConsentRequiredError
from api.app.profile.application.create_profile import (
    CreateProfileCommand,
    CreateProfileUseCase,
)
from api.app.profile.application.upload_photo import (
    UploadPhotoCommand,
    UploadUserPhotoUseCase,
)
from api.app.profile.repositories.profile_repository import ProfileUnitOfWork
from api.app.tryon.application.get_job_status import GetTryOnJobStatusUseCase
from api.app.tryon.application.process_job import ProcessTryOnJobUseCase
from api.app.tryon.application.submit_job import (
    SubmitTryOnJobCommand,
    SubmitTryOnJobUseCase,
)
from api.app.tryon.ports import InferenceInput, InferenceOutput
from api.app.tryon.repositories.tryon_repository import TryOnUnitOfWork
from database.models.catalog import Merchant
from PIL import Image
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


def _create_valid_portrait_bytes() -> bytes:
    # 600x800 RGB portrait image with valid luminance and contrast
    width, height = 600, 800
    color = (150, 120, 100)
    img = Image.new("RGB", (width, height), color)
    for x in range(width // 2):
        for y in range(height):
            img.putpixel(
                (x, y), (max(0, color[0] - 60), max(0, color[1] - 60), max(0, color[2] - 60))
            )
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


class FailingQualityAdapter:
    """Mock adapter returning a blank black frame to trigger quality rejection."""

    model_version = "mock-fail-v1"
    pipeline_version = "pipe-v1"
    is_commercial_cleared = True

    async def execute_tryon(self, payload: InferenceInput) -> InferenceOutput:
        # 512x512 solid black image
        img = Image.new("RGB", (512, 512), (0, 0, 0))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return InferenceOutput(
            rendered_image_bytes=buf.getvalue(),
            model_version=self.model_version,
            pipeline_version=self.pipeline_version,
            inference_latency_ms=100.0,
        )


@pytest.mark.asyncio
async def test_tryon_consent_and_photo_guards(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    profile_uow = ProfileUnitOfWork(session_factory)
    catalog_uow = CatalogUnitOfWork(session_factory)
    tryon_uow = TryOnUnitOfWork(session_factory)

    # 1. Create user with NO body_photo consent
    create_uc = CreateProfileUseCase(profile_uow)
    user_res = await create_uc.execute(
        CreateProfileCommand(
            height_cm=175,
            weight_kg=70,
            consents={"body_photo": False},  # Denied consent
        )
    )
    user_id = user_res.user_id

    submit_uc = SubmitTryOnJobUseCase(tryon_uow, profile_uow, catalog_uow)
    dummy_garment_id = uuid4()

    # Must raise ConsentRequiredError (Rule I07)
    with pytest.raises(ConsentRequiredError):
        await submit_uc.execute(
            SubmitTryOnJobCommand(
                user_id=user_id,
                garment_id=dummy_garment_id,
                idempotency_key="idemp-1",
            )
        )


@pytest.mark.asyncio
async def test_tryon_full_async_lifecycle_and_caching(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    profile_uow = ProfileUnitOfWork(session_factory)
    catalog_uow = CatalogUnitOfWork(session_factory)
    tryon_uow = TryOnUnitOfWork(session_factory)

    # 1. Setup User with Consent and Valid Portrait Photo
    create_uc = CreateProfileUseCase(profile_uow)
    user_res = await create_uc.execute(
        CreateProfileCommand(
            height_cm=180,
            weight_kg=75,
            consents={"body_photo": True, "measurements": True},
        )
    )
    user_id = user_res.user_id

    upload_uc = UploadUserPhotoUseCase(profile_uow)
    photo_bytes = _create_valid_portrait_bytes()
    photo_res = await upload_uc.execute(
        UploadPhotoCommand(
            user_id=user_id,
            photo_type="tryon_reference",
            photo_bytes=photo_bytes,
        )
    )
    assert photo_res.status == "accepted"

    # 2. Ingest & Enrich Garment
    async with catalog_uow:
        merchant = Merchant(name="TryOn Boutique", merchant_type="retailer")
        catalog_uow.merchants.add(merchant)
        await catalog_uow.commit()
        merchant_id = merchant.id

    ingest_uc = IngestMerchantProductUseCase(catalog_uow)
    product_res = await ingest_uc.execute(
        IngestProductCommand(
            merchant_id=merchant_id,
            source_product_id="TRYON-TEE-01",
            title="Premium Cotton Graphic Tee White",
            source_url="https://boutique.com/tee01",
            category="tops",
            price_minor=199900,
        )
    )
    garment_id = product_res.canonical_garment_id

    enrich_uc = EnrichGarmentUseCase(catalog_uow)
    await enrich_uc.execute(EnrichGarmentCommand(garment_id=garment_id))

    # 3. Submit Try-On Job (Rule I06: Non-blocking 202)
    submit_uc = SubmitTryOnJobUseCase(tryon_uow, profile_uow, catalog_uow)
    cmd = SubmitTryOnJobCommand(
        user_id=user_id,
        garment_id=garment_id,
        idempotency_key="idemp-vto-100",
        render_config={"resolution": "512x768"},
    )
    sub_res = await submit_uc.execute(cmd)

    assert sub_res.status == "queued"
    assert sub_res.is_cached is False
    assert sub_res.job_id is not None
    job_id = sub_res.job_id

    # 4. Check Status (Rule I06: Client status polling)
    status_uc = GetTryOnJobStatusUseCase(tryon_uow)
    status_res = await status_uc.execute(job_id)
    assert status_res.status == "queued"

    # 5. Worker Execution (Rule I06, I09, I10)
    process_uc = ProcessTryOnJobUseCase(tryon_uow, profile_uow, catalog_uow)
    garment_thumb_bytes = _create_valid_portrait_bytes()
    proc_res = await process_uc.execute(
        job_id=job_id,
        user_photo_bytes=photo_bytes,
        garment_image_bytes=garment_thumb_bytes,
    )

    assert proc_res.status == "completed"
    assert proc_res.result_url is not None
    assert proc_res.failure_reason is None

    # Verify status is now completed with result_url
    status_after = await status_uc.execute(job_id)
    assert status_after.status == "completed"
    assert status_after.result_url == proc_res.result_url

    # 6. Composite Cache Hit Verification (Roadmap 4.4)
    # Subsequent submission with same photo hash and garment version should hit cache immediately!
    sub_res2 = await submit_uc.execute(
        SubmitTryOnJobCommand(
            user_id=user_id,
            garment_id=garment_id,
            idempotency_key="idemp-vto-200",  # Different idempotency key, same artifact payload
            render_config={"resolution": "512x768"},
        )
    )
    assert sub_res2.is_cached is True
    assert sub_res2.status == "completed"
    assert sub_res2.result_url == proc_res.result_url


@pytest.mark.asyncio
async def test_tryon_post_inference_quality_failure(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    profile_uow = ProfileUnitOfWork(session_factory)
    catalog_uow = CatalogUnitOfWork(session_factory)
    tryon_uow = TryOnUnitOfWork(session_factory)

    # 1. Setup User and Garment
    create_uc = CreateProfileUseCase(profile_uow)
    user_res = await create_uc.execute(
        CreateProfileCommand(
            height_cm=180,
            weight_kg=75,
            consents={"body_photo": True},
        )
    )
    user_id = user_res.user_id

    upload_uc = UploadUserPhotoUseCase(profile_uow)
    await upload_uc.execute(
        UploadPhotoCommand(
            user_id=user_id,
            photo_type="tryon_reference",
            photo_bytes=_create_valid_portrait_bytes(),
        )
    )

    async with catalog_uow:
        merchant = Merchant(name="Shop", merchant_type="retailer")
        catalog_uow.merchants.add(merchant)
        await catalog_uow.commit()
        merchant_id = merchant.id

    ingest_uc = IngestMerchantProductUseCase(catalog_uow)
    product_res = await ingest_uc.execute(
        IngestProductCommand(
            merchant_id=merchant_id,
            source_product_id="ITEM-FAIL-01",
            title="Linen Shirt",
            source_url="https://shop.com/1",
            category="tops",
            price_minor=150000,
        )
    )
    garment_id = product_res.canonical_garment_id

    # 2. Enqueue Job
    submit_uc = SubmitTryOnJobUseCase(tryon_uow, profile_uow, catalog_uow)
    sub_res = await submit_uc.execute(
        SubmitTryOnJobCommand(
            user_id=user_id,
            garment_id=garment_id,
            idempotency_key="idemp-fail-1",
        )
    )

    # 3. Process with failing adapter (Rule I10)
    process_uc = ProcessTryOnJobUseCase(
        tryon_uow,
        profile_uow,
        catalog_uow,
        adapter=FailingQualityAdapter(),
    )
    proc_res = await process_uc.execute(job_id=sub_res.job_id)

    assert proc_res.status == "failed"
    assert proc_res.failure_reason == "quality_rejected"

    status_uc = GetTryOnJobStatusUseCase(tryon_uow)
    status = await status_uc.execute(sub_res.job_id)
    assert status.status == "failed"
    assert status.failure_reason == "quality_rejected"
