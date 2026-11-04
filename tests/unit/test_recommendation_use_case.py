import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from database.models.catalog import Merchant
from fashx.catalog.application.enrich_garment import (
    EnrichGarmentCommand,
    EnrichGarmentUseCase,
)
from fashx.catalog.application.ingest_product import (
    IngestMerchantProductUseCase,
    IngestProductCommand,
)
from fashx.catalog.repositories.catalog_repository import CatalogUnitOfWork
from fashx.profile.application.create_profile import (
    CreateProfileCommand,
    CreateProfileUseCase,
)
from fashx.profile.application.update_preferences import (
    UpdatePreferencesCommand,
    UpdatePreferencesUseCase,
)
from fashx.profile.repositories.profile_repository import ProfileUnitOfWork
from fashx.recommendation.application.generate_feed import (
    GenerateFeedCommand,
    GenerateFeedUseCase,
)


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
        await catalog_uow.flush()
        from database.models.catalog import CatalogSource
        source = CatalogSource(
            slug=f"merchant-{merchant.id}",
            name=merchant.name,
            kind="manual",
            status="cleared",
            rights_display=True,
            rights_tryon=True,
            image_policy="mirror",
        )
        catalog_uow.sources.add(source)
        await catalog_uow.commit()
        merchant_id = merchant.id
        source_id = source.id

    ingest_uc = IngestMerchantProductUseCase(catalog_uow)
    enrich_uc = EnrichGarmentUseCase(catalog_uow)

    # Item A: Ideal Match (Olive Slim Fit Shirt, ₹2,499)
    item_a = await ingest_uc.execute(
        IngestProductCommand(
            merchant_id=merchant_id,
            source_id=source_id,
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
            source_id=source_id,
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
            source_id=source_id,
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
            source_id=source_id,
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


@pytest.mark.asyncio
async def test_feed_cold_start_does_not_use_fake_embedder(
    session_factory: async_sessionmaker[AsyncSession],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Production-mode feed generation must not instantiate FakeEmbedder.
    Cold-start users must still receive eligible catalog products.
    """
    from database.models.catalog import CatalogSource, Merchant
    from fashx.catalog.application.enrich_garment import EnrichGarmentCommand, EnrichGarmentUseCase
    from fashx.catalog.application.ingest_product import (
        IngestMerchantProductUseCase,
        IngestProductCommand,
    )

    profile_uow = ProfileUnitOfWork(session_factory)
    catalog_uow = CatalogUnitOfWork(session_factory)
    create_uc = CreateProfileUseCase(profile_uow)
    user = await create_uc.execute(
        CreateProfileCommand(
            height_cm=175,
            weight_kg=70,
            build="regular",
        )
    )
    async with catalog_uow:
        merchant = Merchant(
            name="RC01 Test Merchant",
            merchant_type="retailer",
        )
        catalog_uow.merchants.add(merchant)
        await catalog_uow.flush()
        source = CatalogSource(
            slug=f"rc01-{merchant.id}",
            name=merchant.name,
            kind="manual",
            status="cleared",
            rights_display=True,
            rights_tryon=True,
            image_policy="mirror",
        )
        catalog_uow.sources.add(source)
        await catalog_uow.commit()
        merchant_id = merchant.id
        source_id = source.id

    ingest_uc = IngestMerchantProductUseCase(catalog_uow)
    enrich_uc = EnrichGarmentUseCase(catalog_uow)
    item = await ingest_uc.execute(
        IngestProductCommand(
            merchant_id=merchant_id,
            source_id=source_id,
            source_product_id="RC01-PROD-01",
            title="Everyday Cotton T-Shirt",
            source_url="https://merchant.com/prod01",
            category="tops",
            price_minor=99900,
        )
    )
    await enrich_uc.execute(EnrichGarmentCommand(garment_id=item.canonical_garment_id))

    # Set ENV to prod to prove GenerateFeedUseCase runs without FakeEmbedder in production
    monkeypatch.setenv("ENV", "prod")

    feed_uc = GenerateFeedUseCase(profile_uow, catalog_uow)
    result = await feed_uc.execute(GenerateFeedCommand(user_id=user.user_id, limit=10))

    assert result.user_id == user.user_id
    assert result.total_candidates >= 1
    assert len(result.items) >= 1
    assert result.items[0].garment_id == item.canonical_garment_id


@pytest.mark.asyncio
async def test_empty_feed_reports_catalog_empty(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    profile_uow = ProfileUnitOfWork(session_factory)
    catalog_uow = CatalogUnitOfWork(session_factory)
    create_uc = CreateProfileUseCase(profile_uow)
    user = await create_uc.execute(
        CreateProfileCommand(
            height_cm=175,
            weight_kg=70,
            build="regular",
        )
    )
    feed_uc = GenerateFeedUseCase(
        profile_uow,
        catalog_uow,
    )
    result = await feed_uc.execute(
        GenerateFeedCommand(
            user_id=user.user_id,
            limit=10,
        )
    )
    assert result.total_candidates == 0
    assert result.items == []
    assert result.empty_reason == "catalog_empty"

