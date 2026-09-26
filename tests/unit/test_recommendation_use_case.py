import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from api.app.catalog.application.enrich_garment import (
    EnrichGarmentCommand,
    EnrichGarmentUseCase,
)
from api.app.catalog.application.ingest_product import (
    IngestMerchantProductUseCase,
    IngestProductCommand,
)
from api.app.catalog.repositories.catalog_repository import CatalogUnitOfWork
from api.app.profile.application.create_profile import (
    CreateProfileCommand,
    CreateProfileUseCase,
)
from api.app.profile.application.update_preferences import (
    UpdatePreferencesCommand,
    UpdatePreferencesUseCase,
)
from api.app.profile.repositories.profile_repository import ProfileUnitOfWork
from api.app.recommendation.application.generate_feed import (
    GenerateFeedCommand,
    GenerateFeedUseCase,
)
from database.models.catalog import Merchant


@pytest.mark.asyncio
async def test_generate_personalized_feed_end_to_end(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    profile_uow = ProfileUnitOfWork(session_factory)
    catalog_uow = CatalogUnitOfWork(session_factory)

    # 1. Create User with Athletic Build & Preferences
    create_uc = CreateProfileUseCase(profile_uow)
    user_res = await create_uc.execute(
        CreateProfileCommand(height_cm=180, weight_kg=78, build="athletic")
    )
    user_id = user_res.user_id

    pref_uc = UpdatePreferencesUseCase(profile_uow)
    await pref_uc.execute(
        UpdatePreferencesCommand(
            user_id=user_id,
            colors_favored=["olive", "navy"],
            colors_avoided=["yellow"],
            categories=["tops", "bottoms"],
            budget_max=300000,  # Max ₹3,000
        )
    )

    # 2. Ingest Catalog Items
    async with catalog_uow:
        merchant = Merchant(name="Fashion Hub", merchant_type="retailer")
        catalog_uow.merchants.add(merchant)
        await catalog_uow.commit()
        merchant_id = merchant.id

    ingest_uc = IngestMerchantProductUseCase(catalog_uow)
    enrich_uc = EnrichGarmentUseCase(catalog_uow)

    # Item A: Ideal Match (Olive Slim Fit Shirt, ₹2,499)
    item_a = await ingest_uc.execute(
        IngestProductCommand(
            merchant_id=merchant_id,
            source_product_id="ITEM-A",
            title="Slim Fit Oxford Olive Cotton Shirt",
            source_url="https://hub.com/a",
            category="tops",
            price_minor=249900,
        )
    )
    await enrich_uc.execute(EnrichGarmentCommand(garment_id=item_a.canonical_garment_id))

    # Item B: Avoided Color (Yellow Casual Shirt, ₹1,999) -> Should be filtered out
    item_b = await ingest_uc.execute(
        IngestProductCommand(
            merchant_id=merchant_id,
            source_product_id="ITEM-B",
            title="Relaxed Fit Yellow Linen Shirt",
            source_url="https://hub.com/b",
            category="tops",
            price_minor=199900,
        )
    )
    await enrich_uc.execute(EnrichGarmentCommand(garment_id=item_b.canonical_garment_id))

    # Item C: Over Budget (Designer Leather Jacket, ₹9,999) -> Should be filtered out
    item_c = await ingest_uc.execute(
        IngestProductCommand(
            merchant_id=merchant_id,
            source_product_id="ITEM-C",
            title="Designer Leather Biker Jacket",
            source_url="https://hub.com/c",
            category="tops",
            price_minor=999900,
        )
    )
    await enrich_uc.execute(EnrichGarmentCommand(garment_id=item_c.canonical_garment_id))

    # Item D: In Budget (Navy Slim Chinos, ₹2,199)
    item_d = await ingest_uc.execute(
        IngestProductCommand(
            merchant_id=merchant_id,
            source_product_id="ITEM-D",
            title="Slim Fit Navy Chinos Pants",
            source_url="https://hub.com/d",
            category="bottoms",
            price_minor=219900,
        )
    )
    await enrich_uc.execute(EnrichGarmentCommand(garment_id=item_d.canonical_garment_id))

    # 3. Generate Personalized Feed
    feed_uc = GenerateFeedUseCase(profile_uow, catalog_uow)
    feed_res = await feed_uc.execute(GenerateFeedCommand(user_id=user_id, limit=10))

    assert feed_res.user_id == user_id
    assert feed_res.total_candidates == 4
    # Yellow shirt (avoided color) and leather jacket (over budget) must be filtered out
    returned_ids = {item.garment_id for item in feed_res.items}
    assert item_a.canonical_garment_id in returned_ids
    assert item_d.canonical_garment_id in returned_ids
    assert item_b.canonical_garment_id not in returned_ids
    assert item_c.canonical_garment_id not in returned_ids

    # Verify Natural Language Stylist Rationales
    top_pick = feed_res.items[0]
    assert top_pick.stylist_explanation is not None
    assert len(top_pick.stylist_explanation) > 15
    assert top_pick.relevance_score > 0.0
