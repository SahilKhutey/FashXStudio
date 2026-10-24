import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from database.models.catalog import Merchant
from fashx.catalog.application.enrich_garment import EnrichGarmentCommand, EnrichGarmentUseCase
from fashx.catalog.application.ingest_product import (
    IngestMerchantProductUseCase,
    IngestProductCommand,
)
from fashx.catalog.repositories.catalog_repository import CatalogUnitOfWork
from fashx.profile.application.create_profile import CreateProfileCommand, CreateProfileUseCase
from fashx.profile.application.update_preferences import (
    UpdatePreferencesCommand,
    UpdatePreferencesUseCase,
)
from fashx.profile.repositories.profile_repository import ProfileUnitOfWork
from fashx.recommendation.application.generate_feed import (
    GenerateFeedCommand,
    GenerateFeedUseCase,
)
from fashx.recommendation.ranker import cosine_similarity


def test_missing_embeddings_are_not_treated_as_real_similarity():
    """Missing vectors must not be mistaken for meaningful semantic matches."""
    assert cosine_similarity(None, [0.1, 0.2]) == 0.5


def test_incompatible_embedding_dimensions_use_existing_fallback():
    """The current cosine helper retains its compatibility fallback."""
    assert cosine_similarity([0.1, 0.2], [0.1, 0.2, 0.3]) == 0.5


def test_identical_nonzero_vectors_have_unit_similarity():
    assert cosine_similarity([1.0, 0.0], [1.0, 0.0]) == pytest.approx(1.0)


def test_orthogonal_vectors_have_zero_similarity():
    assert cosine_similarity([1.0, 0.0], [0.0, 1.0]) == pytest.approx(0.0)


def test_zero_vectors_do_not_produce_nan():
    assert cosine_similarity([0.0, 0.0], [1.0, 0.0]) == 0.0


@pytest.mark.asyncio
async def test_generate_feed_integration_scenarios(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Verify feed generation under explicit preference, budget, and catalog edge cases.

    Scenarios tested:
    1. A user who favors blue garments ranks blue higher.
    2. A user who avoids blue garments has blue excluded by deterministic filter.
    3. A user with budget restrictions has out-of-budget garments excluded.
    4. A user with no recorded preferences (cold-start) still receives valid feed.
    5. Missing embeddings on garments (from heuristic enricher) do not cause errors.
    """
    profile_uow = ProfileUnitOfWork(session_factory)
    catalog_uow = CatalogUnitOfWork(session_factory)

    # Setup Merchant and Catalog
    async with catalog_uow:
        merchant = Merchant(name="Contract Test Merchant", merchant_type="retailer")
        catalog_uow.merchants.add(merchant)
        await catalog_uow.commit()
        merchant_id = merchant.id

    ingest_uc = IngestMerchantProductUseCase(catalog_uow)
    enrich_uc = EnrichGarmentUseCase(catalog_uow)

    # Ingest 3 distinct items
    # Item 1: Blue Cotton Casual Shirt (₹1,500)
    item_blue = await ingest_uc.execute(
        IngestProductCommand(
            merchant_id=merchant_id,
            source_product_id="PROD-BLUE-01",
            title="Navy Blue Cotton Casual Shirt",
            source_url="https://merchant.com/blue",
            category="top",
            price_minor=150000,
        )
    )
    # Enriched without semantic embedding (embedding=None)
    await enrich_uc.execute(EnrichGarmentCommand(garment_id=item_blue.canonical_garment_id))

    # Item 2: Olive Linen Relaxed Shirt (₹2,500)
    item_olive = await ingest_uc.execute(
        IngestProductCommand(
            merchant_id=merchant_id,
            source_product_id="PROD-OLIVE-01",
            title="Olive Green Linen Relaxed Shirt",
            source_url="https://merchant.com/olive",
            category="top",
            price_minor=250000,
        )
    )
    await enrich_uc.execute(EnrichGarmentCommand(garment_id=item_olive.canonical_garment_id))

    # Item 3: Luxury Black Silk Shirt (₹9,000)
    item_expensive = await ingest_uc.execute(
        IngestProductCommand(
            merchant_id=merchant_id,
            source_product_id="PROD-EXP-01",
            title="Black Silk Formal Shirt",
            source_url="https://merchant.com/exp",
            category="top",
            price_minor=900000,
        )
    )
    await enrich_uc.execute(EnrichGarmentCommand(garment_id=item_expensive.canonical_garment_id))

    create_uc = CreateProfileUseCase(profile_uow)
    pref_uc = UpdatePreferencesUseCase(profile_uow)
    feed_uc = GenerateFeedUseCase(profile_uow, catalog_uow)

    # 1. User Favors Blue
    user_blue_res = await create_uc.execute(
        CreateProfileCommand(height_cm=175, weight_kg=70, build="regular")
    )
    await pref_uc.execute(
        UpdatePreferencesCommand(
            user_id=user_blue_res.user_id,
            colors_favored=["blue"],
        )
    )
    feed_blue = await feed_uc.execute(
        GenerateFeedCommand(user_id=user_blue_res.user_id, limit=10)
    )
    assert len(feed_blue.items) >= 2
    # Ensure blue item is ranked higher than olive
    blue_garment_ids = [it.garment_id for it in feed_blue.items]
    assert blue_garment_ids.index(item_blue.canonical_garment_id) < blue_garment_ids.index(
        item_olive.canonical_garment_id
    )

    # 2. User Avoids Blue
    user_avoid_blue = await create_uc.execute(
        CreateProfileCommand(height_cm=175, weight_kg=70, build="regular")
    )
    await pref_uc.execute(
        UpdatePreferencesCommand(
            user_id=user_avoid_blue.user_id,
            colors_avoided=["blue", "navy"],
        )
    )
    feed_avoid = await feed_uc.execute(
        GenerateFeedCommand(user_id=user_avoid_blue.user_id, limit=10)
    )
    avoid_ids = [it.garment_id for it in feed_avoid.items]
    assert item_blue.canonical_garment_id not in avoid_ids
    assert item_olive.canonical_garment_id in avoid_ids

    # 3. User with Budget Restriction (< ₹3,000)
    user_budget = await create_uc.execute(
        CreateProfileCommand(height_cm=175, weight_kg=70, build="regular")
    )
    await pref_uc.execute(
        UpdatePreferencesCommand(
            user_id=user_budget.user_id,
            budget_max=300000,  # ₹3,000
        )
    )
    feed_budget = await feed_uc.execute(
        GenerateFeedCommand(user_id=user_budget.user_id, limit=10)
    )
    budget_ids = [it.garment_id for it in feed_budget.items]
    assert item_expensive.canonical_garment_id not in budget_ids
    assert item_blue.canonical_garment_id in budget_ids
    assert item_olive.canonical_garment_id in budget_ids

    # 4. User with No Preferences (Cold Start)
    user_cold = await create_uc.execute(
        CreateProfileCommand(height_cm=170, weight_kg=65, build="regular")
    )
    feed_cold = await feed_uc.execute(
        GenerateFeedCommand(user_id=user_cold.user_id, limit=10)
    )
    assert len(feed_cold.items) == 3
    # Check that all items have valid explanations and non-empty scores
    for item in feed_cold.items:
        assert item.relevance_score >= 0.0
        assert item.stylist_explanation is not None
