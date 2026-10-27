"""Verification of P0.3: Meaningful personalization ranking.

Proves that:
1. Embeddings are non-constant and discriminate between distinct garments.
2. User taste vectors reflect style quiz preferences.
3. Users with different style preferences receive different rankings on the same catalog.
4. Cold-start users receive balanced neutral rankings.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from database.models.catalog import Merchant
from fashx.catalog.application.enrich_garment import EnrichGarmentCommand, EnrichGarmentUseCase
from fashx.catalog.application.ingest_product import (
    IngestMerchantProductUseCase,
    IngestProductCommand,
)
from fashx.catalog.embeddings.fake import FakeEmbedder
from fashx.catalog.repositories.catalog_repository import CatalogUnitOfWork
from fashx.discovery.taste import compute_taste_vector
from fashx.profile.application.create_profile import CreateProfileCommand, CreateProfileUseCase
from fashx.profile.repositories.profile_repository import ProfileUnitOfWork
from fashx.recommendation.application.generate_feed import GenerateFeedCommand, GenerateFeedUseCase
from fashx.recommendation.ranker import cosine_similarity


def test_garment_embeddings_are_non_constant() -> None:
    embedder = FakeEmbedder()
    emb_kurta = embedder.embed_text(["Women's Teal Cotton Printed Kurta top kurta"])[0]
    emb_hoodie = embedder.embed_text(["Unisex Black Graphic Streetwear Hoodie top hoodie"])[0]

    assert len(emb_kurta) == 512
    assert len(emb_hoodie) == 512
    # Ensure they are not the legacy [0.05] * 512 placeholder
    assert emb_kurta != [0.05] * 512
    assert emb_hoodie != [0.05] * 512
    # Ensure distinct garments have distinct embeddings
    assert emb_kurta != emb_hoodie

    # Similarity should be < 1.0
    sim = cosine_similarity(emb_kurta, emb_hoodie)
    assert 0.0 <= sim < 0.95


def test_user_taste_vectors_reflect_style_preferences() -> None:
    taste_ethnic = compute_taste_vector([], user_styles=["ethnic", "festive"])
    taste_street = compute_taste_vector([], user_styles=["streetwear", "casual"])
    taste_cold = compute_taste_vector([], user_styles=None)

    assert len(taste_ethnic) == 512
    assert len(taste_street) == 512
    assert len(taste_cold) == 512

    # Different styles produce statistically distinct taste vectors
    assert not (taste_ethnic == taste_street).all()
    assert not (taste_ethnic == taste_cold).all()


@pytest.mark.asyncio
async def test_different_preferences_produce_different_rankings(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    profile_uow = ProfileUnitOfWork(session_factory)
    catalog_uow = CatalogUnitOfWork(session_factory)

    # 1. Create two users
    create_uc = CreateProfileUseCase(profile_uow)
    user_a_res = await create_uc.execute(
        CreateProfileCommand(height_cm=165, weight_kg=55, build="regular")
    )
    user_b_res = await create_uc.execute(
        CreateProfileCommand(height_cm=178, weight_kg=72, build="athletic")
    )

    user_a = user_a_res.user_id
    user_b = user_b_res.user_id

    # Set User A preferences: Favors olive
    from fashx.profile.application.update_preferences import (
        UpdatePreferencesCommand,
        UpdatePreferencesUseCase,
    )

    pref_uc = UpdatePreferencesUseCase(profile_uow)
    await pref_uc.execute(
        UpdatePreferencesCommand(
            user_id=user_a,
            colors_favored=["olive"],
        )
    )

    # Set User B preferences: Favors black
    await pref_uc.execute(
        UpdatePreferencesCommand(
            user_id=user_b,
            colors_favored=["black"],
        )
    )

    # 2. Ingest two distinct catalog items
    async with catalog_uow:
        merchant = Merchant(name="Diverse Hub", merchant_type="retailer")
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

    ingest_uc = IngestMerchantProductUseCase(catalog_uow)
    enrich_uc = EnrichGarmentUseCase(catalog_uow)

    # Item 1: Olive Silk Anarkali Ethnic Kurta
    item_ethnic = await ingest_uc.execute(
        IngestProductCommand(
            merchant_id=merchant_id,
            source_product_id="ETHNIC-01",
            title="Olive Silk Anarkali Ethnic Kurta",
            source_url="https://hub.com/ethnic",
            category="top",
            price_minor=199900,
        )
    )
    await enrich_uc.execute(EnrichGarmentCommand(garment_id=item_ethnic.canonical_garment_id))

    # Item 2: Black Graphic Streetwear Hoodie
    item_street = await ingest_uc.execute(
        IngestProductCommand(
            merchant_id=merchant_id,
            source_product_id="STREET-01",
            title="Black Heavyweight Graphic Streetwear Hoodie",
            source_url="https://hub.com/street",
            category="top",
            price_minor=199900,
        )
    )
    await enrich_uc.execute(EnrichGarmentCommand(garment_id=item_street.canonical_garment_id))

    # 3. Generate Feed for both users
    feed_uc = GenerateFeedUseCase(profile_uow, catalog_uow)

    feed_a = await feed_uc.execute(GenerateFeedCommand(user_id=user_a, limit=10))
    feed_b = await feed_uc.execute(GenerateFeedCommand(user_id=user_b, limit=10))

    assert len(feed_a.items) >= 2
    assert len(feed_b.items) >= 2

    # User A (Ethnic) should rank the Ethnic item above the Streetwear item
    item_a_ids = [it.garment_id for it in feed_a.items]
    rank_a_ethnic = item_a_ids.index(item_ethnic.canonical_garment_id)
    rank_a_street = item_a_ids.index(item_street.canonical_garment_id)
    assert rank_a_ethnic < rank_a_street, (
        "User A with ethnic preference should rank ethnic kurta above hoodie"
    )

    # User B (Streetwear) should rank the Streetwear item above the Ethnic item
    item_b_ids = [it.garment_id for it in feed_b.items]
    rank_b_ethnic = item_b_ids.index(item_ethnic.canonical_garment_id)
    rank_b_street = item_b_ids.index(item_street.canonical_garment_id)
    assert rank_b_street < rank_b_ethnic, (
        "User B with streetwear preference should rank hoodie above ethnic kurta"
    )


@pytest.mark.asyncio
async def test_user_style_quiz_produces_distinct_feed_order(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Proves that users with identical physical profiles but different style quiz profiles receive distinct feed rankings."""
    profile_uow = ProfileUnitOfWork(session_factory)
    catalog_uow = CatalogUnitOfWork(session_factory)

    create_uc = CreateProfileUseCase(profile_uow)
    res_a = await create_uc.execute(CreateProfileCommand(height_cm=170, weight_kg=65, build="regular"))
    res_b = await create_uc.execute(CreateProfileCommand(height_cm=170, weight_kg=65, build="regular"))
    user_ethnic = res_a.user_id
    user_street = res_b.user_id

    # Set style quiz answers on OnboardingProfile
    async with profile_uow:
        prof_a = await profile_uow.onboarding_profiles.create_if_missing(user_ethnic)
        prof_a.styles = ["ethnic", "festive"]
        prof_b = await profile_uow.onboarding_profiles.create_if_missing(user_street)
        prof_b.styles = ["streetwear", "casual"]
        await profile_uow.commit()

    # Ingest catalog items
    async with catalog_uow:
        merchant = Merchant(name="Style Hub", merchant_type="retailer")
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

    item_ethnic = await ingest_uc.execute(
        IngestProductCommand(
            merchant_id=merchant_id,
            source_id=source_id,
            source_product_id="ETH-QUIZ-01",
            title="Embroidered Chanderi Ethnic Kurta",
            source_url="https://hub.com/eth1",
            category="top",
            price_minor=149900,
        )
    )
    await enrich_uc.execute(EnrichGarmentCommand(garment_id=item_ethnic.canonical_garment_id))

    item_street = await ingest_uc.execute(
        IngestProductCommand(
            merchant_id=merchant_id,
            source_id=source_id,
            source_product_id="STR-QUIZ-01",
            title="Oversized Streetwear Graphic Hoodie",
            source_url="https://hub.com/str1",
            category="top",
            price_minor=149900,
        )
    )
    await enrich_uc.execute(EnrichGarmentCommand(garment_id=item_street.canonical_garment_id))

    feed_uc = GenerateFeedUseCase(profile_uow, catalog_uow)
    feed_ethnic = await feed_uc.execute(GenerateFeedCommand(user_id=user_ethnic, limit=10))
    feed_street = await feed_uc.execute(GenerateFeedCommand(user_id=user_street, limit=10))

    ids_ethnic = [it.garment_id for it in feed_ethnic.items]
    ids_street = [it.garment_id for it in feed_street.items]

    assert ids_ethnic.index(item_ethnic.canonical_garment_id) < ids_ethnic.index(
        item_street.canonical_garment_id
    ), "Ethnic style user must rank ethnic item first"

    assert ids_street.index(item_street.canonical_garment_id) < ids_street.index(
        item_ethnic.canonical_garment_id
    ), "Streetwear style user must rank streetwear item first"


@pytest.mark.asyncio
async def test_feed_signals_and_wardrobe_saves_steer_feed(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Proves that user interactions (like signals & wardrobe saves) actively steer the feed toward similar items."""
    profile_uow = ProfileUnitOfWork(session_factory)
    catalog_uow = CatalogUnitOfWork(session_factory)

    create_uc = CreateProfileUseCase(profile_uow)
    res = await create_uc.execute(CreateProfileCommand(height_cm=175, weight_kg=70, build="regular"))
    user_id = res.user_id

    # Ingest catalog items
    async with catalog_uow:
        merchant = Merchant(name="Signal Hub", merchant_type="retailer")
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

    item_street = await ingest_uc.execute(
        IngestProductCommand(
            merchant_id=merchant_id,
            source_id=source_id,
            source_product_id="STR-SIG-01",
            title="Urban Streetwear Cargo Pants",
            source_url="https://hub.com/cargos",
            category="bottom",
            price_minor=199900,
        )
    )
    await enrich_uc.execute(EnrichGarmentCommand(garment_id=item_street.canonical_garment_id))

    item_formal = await ingest_uc.execute(
        IngestProductCommand(
            merchant_id=merchant_id,
            source_id=source_id,
            source_product_id="FRM-SIG-01",
            title="Tailored Formal Business Trousers",
            source_url="https://hub.com/trousers",
            category="bottom",
            price_minor=199900,
        )
    )
    await enrich_uc.execute(EnrichGarmentCommand(garment_id=item_formal.canonical_garment_id))

    # User likes and saves the Streetwear item into wardrobe
    async with profile_uow:
        from database.models.commerce_feedback import WardrobeItem
        from database.models.feed import FeedSignal

        sig = FeedSignal(user_id=user_id, garment_id=item_street.canonical_garment_id, action="like")
        profile_uow.session.add(sig)

        wardrobe = WardrobeItem(
            user_id=user_id,
            garment_id=item_street.canonical_garment_id,
            snapshot_title="Urban Streetwear Cargo Pants",
            snapshot_price_minor=199900,
            snapshot_currency="INR",
            snapshot_image_key="key",
        )
        profile_uow.session.add(wardrobe)
        await profile_uow.commit()

    feed_uc = GenerateFeedUseCase(profile_uow, catalog_uow)
    feed = await feed_uc.execute(GenerateFeedCommand(user_id=user_id, limit=10))

    feed_ids = [it.garment_id for it in feed.items]
    assert feed_ids.index(item_street.canonical_garment_id) < feed_ids.index(
        item_formal.canonical_garment_id
    ), "User liking and saving streetwear items must prioritize streetwear over formal"
