import io

import pytest
from PIL import Image
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from fashx.catalog.application.enrich_garment import (
    EnrichGarmentCommand,
    EnrichGarmentUseCase,
)
from fashx.catalog.application.ingest_product import (
    IngestMerchantProductUseCase,
    IngestProductCommand,
)
from fashx.catalog.repositories.catalog_repository import CatalogUnitOfWork
from api.app.commerce_wardrobe.application.create_buy_click import (
    CreateBuyClickCommand,
    CreateBuyClickUseCase,
)
from api.app.commerce_wardrobe.application.list_wardrobe import ListWardrobeUseCase
from api.app.commerce_wardrobe.application.save_to_wardrobe import (
    SaveToWardrobeCommand,
    SaveToWardrobeUseCase,
)
from api.app.commerce_wardrobe.application.submit_fit_feedback import (
    SubmitFitFeedbackCommand,
    SubmitFitFeedbackUseCase,
)
from api.app.commerce_wardrobe.application.submit_tryon_feedback import (
    SubmitTryOnFeedbackCommand,
    SubmitTryOnFeedbackUseCase,
)
from api.app.commerce_wardrobe.repositories.commerce_wardrobe_repository import (
    CommerceWardrobeUnitOfWork,
)
from api.app.core.ports.storage import InMemoryStorageAdapter
from api.app.profile.application.create_profile import (
    CreateProfileCommand,
    CreateProfileUseCase,
)
from api.app.profile.application.revoke_consent import (
    RevokeConsentCommand,
    RevokeConsentUseCase,
)
from api.app.profile.application.update_preferences import (
    UpdatePreferencesCommand,
    UpdatePreferencesUseCase,
)
from api.app.profile.application.upload_photo import (
    UploadPhotoCommand,
    UploadUserPhotoUseCase,
)
from api.app.profile.repositories.profile_repository import ProfileUnitOfWork
from api.app.recommendation.application.generate_feed import (
    GenerateFeedCommand,
    GenerateFeedUseCase,
)
from api.app.tryon.application.get_job_status import GetTryOnJobStatusUseCase
from api.app.tryon.application.process_job import ProcessTryOnJobUseCase
from api.app.tryon.application.submit_job import (
    SubmitTryOnJobCommand,
    SubmitTryOnJobUseCase,
)
from api.app.tryon.repositories.tryon_repository import TryOnUnitOfWork
from database.models.catalog import Brand, Merchant


def _generate_valid_portrait() -> bytes:
    img = Image.new("RGB", (600, 800), (145, 120, 100))
    for x in range(300):
        for y in range(800):
            img.putpixel((x, y), (85, 60, 40))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.mark.asyncio
async def test_full_system_journey_end_to_end(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Rule I18 & Gate G1: Validates complete end-to-end consumer lifecycle in a single transactional run."""
    profile_uow = ProfileUnitOfWork(session_factory)
    catalog_uow = CatalogUnitOfWork(session_factory)
    tryon_uow = TryOnUnitOfWork(session_factory)
    commerce_uow = CommerceWardrobeUnitOfWork(session_factory)
    storage = InMemoryStorageAdapter()

    # =========================================================================
    # Step 1: User Onboarding & Biometrics
    # =========================================================================
    create_profile_uc = CreateProfileUseCase(profile_uow)
    user_res = await create_profile_uc.execute(
        CreateProfileCommand(
            height_cm=182,
            weight_kg=78,
            build="athletic",
            consents={"body_photo": True, "measurements": True},
        )
    )
    user_id = user_res.user_id
    assert user_res.build == "athletic"

    # =========================================================================
    # Step 2: Photo Upload, Quality Gate & Monk Skin Tone Calibration
    # =========================================================================
    upload_photo_uc = UploadUserPhotoUseCase(profile_uow, storage)
    photo_bytes = _generate_valid_portrait()
    photo_res = await upload_photo_uc.execute(
        UploadPhotoCommand(
            user_id=user_id,
            photo_type="tryon_reference",
            photo_bytes=photo_bytes,
        )
    )
    assert photo_res.status == "accepted"
    assert photo_res.skin_tone is not None
    assert photo_res.skin_tone.monk_scale_index in range(1, 11)

    # =========================================================================
    # Step 3: Style Preferences
    # =========================================================================
    pref_uc = UpdatePreferencesUseCase(profile_uow)
    await pref_uc.execute(
        UpdatePreferencesCommand(
            user_id=user_id,
            colors_favored=["olive", "navy"],
            colors_avoided=["yellow"],
            categories=["tops", "bottoms"],
            budget_max=400000,  # ₹4,000 max
        )
    )

    # =========================================================================
    # Step 4: Merchant Catalog Ingestion & VLM Enrichment
    # =========================================================================
    async with catalog_uow:
        merchant = Merchant(name="Apex Fashion Studio", merchant_type="brand")
        catalog_uow.merchants.add(merchant)
        brand = Brand(name="Apex Fashion Studio", normalized_name="apex_fashion_studio")
        catalog_uow.session.add(brand)
        await catalog_uow.commit()
        merchant_id = merchant.id
        brand_id = brand.id

    ingest_uc = IngestMerchantProductUseCase(catalog_uow)
    product_res = await ingest_uc.execute(
        IngestProductCommand(
            merchant_id=merchant_id,
            brand_id=brand_id,
            source_product_id="APEX-SHIRT-01",
            title="Slim Fit Olive Oxford Shirt",
            source_url="https://apexfashion.com/products/olive-oxford",
            category="tops",
            price_minor=299900,
        )
    )
    garment_id = product_res.canonical_garment_id

    enrich_uc = EnrichGarmentUseCase(catalog_uow)
    enrich_res = await enrich_uc.execute(EnrichGarmentCommand(garment_id=garment_id))
    assert enrich_res.attributes.get("dominant_color") == "olive"
    assert enrich_res.attributes.get("silhouette") == "slim"

    async with catalog_uow:
        offers = await catalog_uow.offers.list_for_garment(garment_id)
        offer_id = offers[0].id

    # =========================================================================
    # Step 5: Personalized 3-Stage Discovery Feed with Stylist Explanations
    # =========================================================================
    feed_uc = GenerateFeedUseCase(profile_uow, catalog_uow)
    feed = await feed_uc.execute(GenerateFeedCommand(user_id=user_id, limit=10))

    assert len(feed.items) >= 1
    top_item = feed.items[0]
    assert top_item.garment_id == garment_id
    assert len(top_item.stylist_explanation) > 10  # Meaningful explanation generated

    # =========================================================================
    # Step 6: Virtual Try-On (VTO Asynchronous Execution)
    # =========================================================================
    submit_tryon_uc = SubmitTryOnJobUseCase(tryon_uow, profile_uow, catalog_uow)
    sub_job = await submit_tryon_uc.execute(
        SubmitTryOnJobCommand(
            user_id=user_id,
            garment_id=garment_id,
            idempotency_key="e2e-tryon-key-1",
        )
    )
    assert sub_job.status == "queued"
    assert sub_job.is_cached is False

    process_tryon_uc = ProcessTryOnJobUseCase(tryon_uow, profile_uow, catalog_uow)
    garment_bytes = _generate_valid_portrait()
    proc_job = await process_tryon_uc.execute(
        job_id=sub_job.job_id,
        user_photo_bytes=photo_bytes,
        garment_image_bytes=garment_bytes,
    )
    assert proc_job.status == "completed"
    assert proc_job.result_url is not None

    status_uc = GetTryOnJobStatusUseCase(tryon_uow)
    status_res = await status_uc.execute(sub_job.job_id)
    assert status_res.status == "completed"

    # Step 6b: Composite Cache Hit Verification
    repeat_sub = await submit_tryon_uc.execute(
        SubmitTryOnJobCommand(
            user_id=user_id,
            garment_id=garment_id,
            idempotency_key="e2e-tryon-key-2",  # Different request, identical content
        )
    )
    assert repeat_sub.is_cached is True
    assert repeat_sub.status == "completed"

    # =========================================================================
    # Step 7: Virtual Closet (Wardrobe Snapshotting)
    # =========================================================================
    wardrobe_save_uc = SaveToWardrobeUseCase(commerce_uow, profile_uow, catalog_uow)
    wardrobe_item = await wardrobe_save_uc.execute(
        SaveToWardrobeCommand(
            user_id=user_id,
            garment_id=garment_id,
            offer_id=offer_id,
        )
    )
    assert wardrobe_item.snapshot_price_minor == 299900
    assert "Olive" in wardrobe_item.snapshot_title

    wardrobe_list_uc = ListWardrobeUseCase(commerce_uow)
    wardrobe_items = await wardrobe_list_uc.execute(user_id)
    assert len(wardrobe_items) == 1

    # =========================================================================
    # Step 8: Outbound Merchant Buy Click & Affiliate Tracking
    # =========================================================================
    buy_click_uc = CreateBuyClickUseCase(commerce_uow, profile_uow, catalog_uow)
    click_res = await buy_click_uc.execute(
        CreateBuyClickCommand(
            user_id=user_id,
            garment_id=garment_id,
            offer_id=offer_id,
        )
    )
    assert "fashx_" in click_res.tracking_id
    assert "utm_source=fashx" in click_res.redirect_url

    # =========================================================================
    # Step 9: Granular Fit Feedback Ledger & Real-Time Brand Sizing Calibration
    # =========================================================================
    fit_feedback_uc = SubmitFitFeedbackUseCase(commerce_uow)
    async with catalog_uow:
        garment = await catalog_uow.canonical_garments.get_by_id(garment_id)
        brand_id = garment.brand_id

    fit_res = await fit_feedback_uc.execute(
        SubmitFitFeedbackCommand(
            user_id=user_id,
            garment_id=garment_id,
            brand_id=brand_id,
            category="tops",
            size_label="L",
            verdict="true_to_size",
            buy_click_id=click_res.buy_click_id,
        )
    )
    assert fit_res.verdict == "true_to_size"
    assert fit_res.brand_recommendation == "true_to_size"

    # Step 9b: Try-On Realism Feedback
    tryon_fb_uc = SubmitTryOnFeedbackUseCase(commerce_uow)
    fb_res = await tryon_fb_uc.execute(
        SubmitTryOnFeedbackCommand(
            user_id=user_id,
            tryon_job_id=sub_job.job_id,
            visual_accuracy="very_accurate",
            purchase_confidence=5,
        )
    )
    assert fb_res.visual_accuracy == "very_accurate"
    assert fb_res.purchase_confidence == 5

    # =========================================================================
    # Step 10: Privacy Gate & Cascading Hard Erasure (Rule I16 & Gate G4)
    # =========================================================================
    revoke_uc = RevokeConsentUseCase(profile_uow, tryon_uow, storage)
    revoke_res = await revoke_uc.execute(
        RevokeConsentCommand(user_id=user_id, data_type="body_photo")
    )
    assert revoke_res.status == "revoked_and_purged"
    assert revoke_res.photos_purged >= 1

    # Verify zero residual photos in DB and Storage
    async with profile_uow:
        photos = await profile_uow.photos.list_for_user(user_id)
        assert len(photos) == 0
        has_consent = await profile_uow.consents.has_consent(user_id, "body_photo")
        assert has_consent is False

    assert await storage.exists(photo_res.storage_key) is False
