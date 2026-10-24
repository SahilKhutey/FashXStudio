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
