from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from database.models.catalog import Brand, CatalogSource, Merchant, MerchantOffer, MerchantProduct
from fashx.catalog.application.ingest_product import (
    IngestMerchantProductUseCase,
    IngestProductCommand,
)
from fashx.catalog.repositories.catalog_repository import CatalogUnitOfWork
from fashx.commerce_wardrobe.application.create_buy_click import (
    CreateBuyClickCommand,
    CreateBuyClickUseCase,
)
from fashx.commerce_wardrobe.application.list_wardrobe import ListWardrobeUseCase
from fashx.commerce_wardrobe.application.mark_purchased import (
    MarkPurchasedCommand,
    MarkPurchasedUseCase,
)
from fashx.commerce_wardrobe.application.save_to_wardrobe import (
    SaveToWardrobeCommand,
    SaveToWardrobeUseCase,
)
from fashx.commerce_wardrobe.application.submit_fit_feedback import (
    SubmitFitFeedbackCommand,
    SubmitFitFeedbackUseCase,
)
from fashx.commerce_wardrobe.repositories.commerce_wardrobe_repository import (
    CommerceWardrobeUnitOfWork,
)
from fashx.core.errors import EntityNotFoundError, ValidationError
from fashx.profile.application.create_profile import (
    CreateProfileCommand,
    CreateProfileUseCase,
)
from fashx.profile.repositories.profile_repository import ProfileUnitOfWork


@pytest.mark.asyncio
async def test_wardrobe_mark_purchased_idempotent_and_cross_user(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    profile_uow = ProfileUnitOfWork(session_factory)
    catalog_uow = CatalogUnitOfWork(session_factory)
    wardrobe_uow = CommerceWardrobeUnitOfWork(session_factory)

    # 1. Setup User A and User B
    create_uc = CreateProfileUseCase(profile_uow)
    user_a = await create_uc.execute(CreateProfileCommand(height_cm=175, weight_kg=70))
    user_b = await create_uc.execute(CreateProfileCommand(height_cm=160, weight_kg=55))

    # 2. Ingest Garment
    async with catalog_uow:
        merchant = Merchant(name="Slice3 Merchant", merchant_type="retailer")
        catalog_uow.merchants.add(merchant)
        await catalog_uow.commit()
        merchant_id = merchant.id

    ingest_uc = IngestMerchantProductUseCase(catalog_uow)
    product = await ingest_uc.execute(
        IngestProductCommand(
            merchant_id=merchant_id,
            source_product_id="ITEM-S3-01",
            title="Linen Relaxed Shirt",
            source_url="https://merchant.com/linen-shirt",
            category="tops",
            price_minor=249900,
        )
    )

    # 3. User A saves garment
    save_uc = SaveToWardrobeUseCase(wardrobe_uow, profile_uow, catalog_uow)
    saved = await save_uc.execute(
        SaveToWardrobeCommand(
            user_id=user_a.user_id,
            garment_id=product.canonical_garment_id,
        )
    )

    mark_uc = MarkPurchasedUseCase(wardrobe_uow)

    # 4. Cross-user: User B cannot mark User A's item as purchased
    with pytest.raises(EntityNotFoundError):
        await mark_uc.execute(
            MarkPurchasedCommand(
                user_id=user_b.user_id,
                item_id=saved.item_id,
                purchased=True,
            )
        )

    # 5. User A marks item as purchased
    res1 = await mark_uc.execute(
        MarkPurchasedCommand(
            user_id=user_a.user_id,
            item_id=saved.item_id,
            purchased=True,
        )
    )
    assert res1.purchased_at is not None
    ts1 = res1.purchased_at

    # 6. Idempotent call retains purchase timestamp
    res2 = await mark_uc.execute(
        MarkPurchasedCommand(
            user_id=user_a.user_id,
            item_id=saved.item_id,
            purchased=True,
        )
    )
    assert res2.purchased_at is not None
    # Compare ISO strings or naive datetimes to be database-agnostic (SQLite naive vs Postgres TZ)
    assert (
        res2.purchased_at.replace(tzinfo=None)
        == ts1.replace(tzinfo=None)
    )


@pytest.mark.asyncio
async def test_closet_list_includes_purchased_and_fit_feedback(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    profile_uow = ProfileUnitOfWork(session_factory)
    catalog_uow = CatalogUnitOfWork(session_factory)
    wardrobe_uow = CommerceWardrobeUnitOfWork(session_factory)

    create_uc = CreateProfileUseCase(profile_uow)
    user = await create_uc.execute(CreateProfileCommand(height_cm=170, weight_kg=65))

    async with catalog_uow:
        merchant = Merchant(name="Slice3 Clothier", merchant_type="brand")
        catalog_uow.merchants.add(merchant)
        await catalog_uow.commit()
        merchant_id = merchant.id

    ingest_uc = IngestMerchantProductUseCase(catalog_uow)
    product = await ingest_uc.execute(
        IngestProductCommand(
            merchant_id=merchant_id,
            source_product_id="ITEM-S3-02",
            title="Pleated Trousers",
            source_url="https://merchant.com/pleated",
            category="bottoms",
            price_minor=399900,
        )
    )

    save_uc = SaveToWardrobeUseCase(wardrobe_uow, profile_uow, catalog_uow)
    saved = await save_uc.execute(
        SaveToWardrobeCommand(
            user_id=user.user_id,
            garment_id=product.canonical_garment_id,
        )
    )

    # Mark purchased
    mark_uc = MarkPurchasedUseCase(wardrobe_uow)
    await mark_uc.execute(
        MarkPurchasedCommand(
            user_id=user.user_id,
            item_id=saved.item_id,
            purchased=True,
        )
    )

    list_uc = ListWardrobeUseCase(wardrobe_uow, catalog_uow=catalog_uow)
    items = await list_uc.execute(user.user_id)

    assert len(items) == 1
    item = items[0]
    assert item.title_at_save == "Pleated Trousers"
    assert item.price_at_save == 399900
    assert item.current_price == 399900
    assert item.purchased_at is not None
    assert item.fit_feedback_given is False
    assert item.render is None  # no tryon render attached


@pytest.mark.asyncio
async def test_fit_feedback_submission_and_duplicate_check(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    profile_uow = ProfileUnitOfWork(session_factory)
    wardrobe_uow = CommerceWardrobeUnitOfWork(session_factory)

    create_uc = CreateProfileUseCase(profile_uow)
    user = await create_uc.execute(CreateProfileCommand(height_cm=180, weight_kg=80))

    brand_id = uuid4()
    garment_id = uuid4()

    submit_uc = SubmitFitFeedbackUseCase(wardrobe_uow)
    res = await submit_uc.execute(
        SubmitFitFeedbackCommand(
            user_id=user.user_id,
            garment_id=garment_id,
            brand_id=brand_id,
            category="tops",
            size_label="L",
            verdict="true_to_size",
        )
    )
    assert res.feedback_id is not None
    assert res.verdict == "true_to_size"

    # Verify duplicate feedback can be detected
    async with wardrobe_uow:
        existing = await wardrobe_uow.fit_feedback.get_by_user_and_garment(user.user_id, garment_id)
        assert existing is not None


@pytest.mark.asyncio
async def test_buy_clicks_refuses_suspended_source_garment(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    profile_uow = ProfileUnitOfWork(session_factory)
    catalog_uow = CatalogUnitOfWork(session_factory)
    commerce_uow = CommerceWardrobeUnitOfWork(session_factory)

    create_uc = CreateProfileUseCase(profile_uow)
    user = await create_uc.execute(CreateProfileCommand(height_cm=170, weight_kg=60))

    async with catalog_uow:
        # Create a suspended source
        source = CatalogSource(
            name="Suspended Vendor",
            slug="suspended-vendor",
            kind="api",
            status="suspended",
        )
        catalog_uow.sources.add(source)

        merchant = Merchant(name="Suspended Merchant", merchant_type="retailer")
        catalog_uow.merchants.add(merchant)

        brand = Brand(name="Suspended Brand", normalized_name="suspended_brand")
        catalog_uow.session.add(brand)
        await catalog_uow.commit()

        # Add product and offer attached to suspended source
        garment_id = uuid4()
        prod = MerchantProduct(
            merchant_id=merchant.id,
            brand_id=brand.id,
            source_id=source.id,
            source_product_id="SUSP-01",
            title="Suspended Coat",
            source_url="https://suspended.com/coat",
            status="active",
        )
        catalog_uow.merchant_products.add(prod)

        offer = MerchantOffer(
            garment_id=garment_id,
            merchant_id=merchant.id,
            source_product_id="SUSP-01",
            url="https://suspended.com/coat",
            price_minor=999900,
            currency="INR",
            in_stock=True,
        )
        catalog_uow.offers.add(offer)
        await catalog_uow.commit()
        offer_id = offer.id

    buy_uc = CreateBuyClickUseCase(commerce_uow, profile_uow, catalog_uow)

    # Must refuse suspended-source garment
    with pytest.raises(ValidationError) as exc_info:
        await buy_uc.execute(
            CreateBuyClickCommand(
                user_id=user.user_id,
                garment_id=garment_id,
                offer_id=offer_id,
            )
        )

    assert "requires cleared status" in str(exc_info.value)
