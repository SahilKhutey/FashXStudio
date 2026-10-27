from __future__ import annotations

from uuid import UUID, uuid4

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from database.models.catalog import (
    CanonicalGarment,
    CatalogSource,
    Merchant,
    MerchantOffer,
    MerchantProduct,
    StyleQuizPick,
)
from database.models.feed import FeedSignal
from database.models.identity import User
from fashx.catalog.repositories.catalog_repository import CatalogUnitOfWork
from fashx.core.database import get_session_factory
from fashx.profile.repositories.profile_repository import ProfileUnitOfWork
from fashx.recommendation.application.generate_feed import (
    GenerateFeedCommand,
    GenerateFeedUseCase,
)
from fashx.recommendation.compatibility import CompatibilityScore
from fashx.recommendation.feed_router import feed_router
from fashx.recommendation.filters import CandidateItem
from fashx.recommendation.scoring import (
    compute_explainable_score,
    fallback_text_embedding,
)
from fashx.security.deps import get_identity_repo, get_principal
from fashx.security.errors import ApiError, api_error_handler
from fashx.security.identity import InMemoryIdentityRepo
from tests.conftest import make_token


@pytest.mark.asyncio
async def test_list_feed_candidates_strict_filtering(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """MVP 3.1: list_feed_candidates requires cleared source, display rights, active & in-stock garments and offers."""
    catalog_uow = CatalogUnitOfWork(session_factory)

    async with catalog_uow:
        merchant = Merchant(name="TestMerchant", merchant_type="retailer")
        catalog_uow.merchants.add(merchant)

        src_cleared = CatalogSource(name="Cleared Source", slug=f"cleared-{uuid4().hex[:6]}", kind="partner", status="cleared", rights_display=True, rights_tryon=True)
        src_nodisplay = CatalogSource(name="NoDisplay Source", slug=f"nodisplay-{uuid4().hex[:6]}", kind="partner", status="cleared", rights_display=False, rights_tryon=True)
        catalog_uow.sources.add(src_cleared)
        catalog_uow.sources.add(src_nodisplay)
        await catalog_uow.commit()

    async with catalog_uow:
        async def make_garment(source_id: UUID, sku: str, active: bool, g_stock: bool, o_stock: bool) -> CanonicalGarment:
            g = CanonicalGarment(display_name=f"Garment {sku}", category="tops", active=active, in_stock=g_stock)
            catalog_uow.canonical_garments.add(g)
            await catalog_uow.canonical_garments.flush()

            prod = MerchantProduct(
                merchant_id=merchant.id,
                canonical_garment_id=g.id,
                source_id=source_id,
                source_product_id=sku,
                title=f"Product {sku}",
                source_url=f"https://example.com/products/{sku}",
                status="active",
            )
            catalog_uow.merchant_products.add(prod)
            await catalog_uow.merchant_products.flush()

            offer = MerchantOffer(
                garment_id=g.id,
                merchant_id=merchant.id,
                source_product_id=sku,
                url=f"https://example.com/{sku}",
                price_minor=50000,
                in_stock=o_stock,
            )
            catalog_uow.offers.add(offer)
            await catalog_uow.offers.flush()
            return g

        # Eligible
        g_valid = await make_garment(src_cleared.id, "SKU-VALID", active=True, g_stock=True, o_stock=True)
        # Ineligible due to inactive garment
        g_inactive = await make_garment(src_cleared.id, "SKU-INACTIVE", active=False, g_stock=True, o_stock=True)
        # Ineligible due to garment out of stock
        g_nostock = await make_garment(src_cleared.id, "SKU-NOSTOCK", active=True, g_stock=False, o_stock=True)
        # Ineligible due to offer out of stock
        g_offernostock = await make_garment(src_cleared.id, "SKU-OFFERNOSTOCK", active=True, g_stock=True, o_stock=False)
        # Ineligible due to no display rights
        g_nodisplay = await make_garment(src_nodisplay.id, "SKU-NODISPLAY", active=True, g_stock=True, o_stock=True)
        await catalog_uow.commit()

    async with catalog_uow:
        candidates = await catalog_uow.canonical_garments.list_feed_candidates(limit=50)
        candidate_ids = {c.id for c in candidates}

        assert g_valid.id in candidate_ids
        assert g_inactive.id not in candidate_ids
        assert g_nostock.id not in candidate_ids
        assert g_offernostock.id not in candidate_ids
        assert g_nodisplay.id not in candidate_ids


@pytest.mark.asyncio
async def test_feed_signals_endpoint_transactional(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """MVP 3.2: POST /api/v1/feed/signals records signal transactionally and fails closed."""
    app = FastAPI()
    app.add_exception_handler(ApiError, api_error_handler)
    repo = InMemoryIdentityRepo()
    app.dependency_overrides[get_identity_repo] = lambda: repo
    app.dependency_overrides[get_session_factory] = lambda: session_factory
    app.include_router(feed_router, prefix="/api/v1", dependencies=[Depends(get_principal)])
    client = TestClient(app)

    identity = await repo.resolve("fashx-test", "user-sig-test")
    user_id = UUID(identity.user_id)
    token = make_token(sub="user-sig-test")
    garment_id = uuid4()

    # 1. Unauthenticated -> 401
    resp_unauth = client.post(
        "/api/v1/feed/signals",
        json={"garment_id": str(garment_id), "action": "like"},
        headers={"Authorization": ""},
    )
    assert resp_unauth.status_code == 401

    # 2. Authenticated -> 201
    resp = client.post(
        "/api/v1/feed/signals",
        json={"garment_id": str(garment_id), "action": "like"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "recorded"
    assert data["user_id"] == str(user_id)
    assert data["garment_id"] == str(garment_id)
    assert data["action"] == "like"

    # Verify persisted in database
    async with session_factory() as session:
        signals = (
            await session.scalars(
                select(FeedSignal).where(
                    FeedSignal.user_id == user_id,
                    FeedSignal.garment_id == garment_id,
                )
            )
        ).all()
        assert len(signals) == 1
        assert signals[0].action == "like"


@pytest.mark.asyncio
async def test_generate_feed_excludes_negative_signals_and_picks(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """MVP 3.3 & 3.5: Feed generation excludes items marked hide/not_interested or disliked in style quiz."""
    profile_uow = ProfileUnitOfWork(session_factory)
    catalog_uow = CatalogUnitOfWork(session_factory)
    user_id = uuid4()

    async with profile_uow:
        profile_uow.users.add(User(id=user_id))
        await profile_uow.commit()

    async with catalog_uow:
        merchant = Merchant(name="M3", merchant_type="retailer")
        catalog_uow.merchants.add(merchant)
        source = CatalogSource(name="S3", slug=f"s3-{uuid4().hex[:6]}", kind="partner", status="cleared", rights_display=True, rights_tryon=True)
        catalog_uow.sources.add(source)
        await catalog_uow.commit()

    async with catalog_uow:
        async def create_garment(sku: str) -> CanonicalGarment:
            g = CanonicalGarment(display_name=f"Garment {sku}", category="tops", active=True, in_stock=True)
            catalog_uow.canonical_garments.add(g)
            await catalog_uow.canonical_garments.flush()
            prod = MerchantProduct(
                merchant_id=merchant.id,
                canonical_garment_id=g.id,
                source_id=source.id,
                source_product_id=sku,
                title=f"Product {sku}",
                source_url=f"https://example.com/products/{sku}",
                status="active",
            )
            catalog_uow.merchant_products.add(prod)
            offer = MerchantOffer(garment_id=g.id, merchant_id=merchant.id, source_product_id=sku, url=f"https://ex.com/{sku}", price_minor=20000, in_stock=True)
            catalog_uow.offers.add(offer)
            await catalog_uow.offers.flush()
            return g

        g_keep = await create_garment("SKU-KEEP")
        g_hidden = await create_garment("SKU-HIDDEN")
        g_quiz_disliked = await create_garment("SKU-QUIZ-DISLIKED")
        await catalog_uow.commit()

    # Record negative feed signal for g_hidden
    async with session_factory() as session:
        session.add(FeedSignal(user_id=user_id, garment_id=g_hidden.id, action="hide"))
        # Record negative style quiz pick for g_quiz_disliked
        session.add(StyleQuizPick(user_id=user_id, garment_id=g_quiz_disliked.id, liked=False))
        await session.commit()

    use_case = GenerateFeedUseCase(profile_uow, catalog_uow)
    cmd = GenerateFeedCommand(user_id=user_id, limit=10)
    result = await use_case.execute(cmd)

    returned_ids = {item.garment_id for item in result.items}
    assert g_keep.id in returned_ids
    assert g_hidden.id not in returned_ids, "Hidden garment must be excluded from feed"
    assert g_quiz_disliked.id not in returned_ids, "Disliked quiz pick must be excluded from feed"


def test_explainable_scoring_bounds_and_grounded_chips() -> None:
    """MVP 3.4: Scoring is bounded in [0.0, 1.0] and produces grounded, non-hallucinated reason chips."""
    cand = CandidateItem(
        garment_id=uuid4(),
        category="tops",
        subcategory="formal_shirts",
        price_minor=250000,
        in_stock=True,
        dominant_color="blue",
        silhouette="tailored",
        title="Oxford Shirt",
    )
    compat = CompatibilityScore(
        color_score=0.95,
        silhouette_score=0.90,
        total_score=0.92,
        color_reason="Blue complements undertone",
        silhouette_reason="Tailored cut matches build",
    )
    taste_vector = [0.1] * 64

    # Scoring with taste signal
    breakdown = compute_explainable_score(
        item=cand,
        compatibility=compat,
        taste_vector=taste_vector,
        has_taste_signal=True,
    )
    assert 0.0 <= breakdown.relevance_score <= 1.0
    assert 0.0 <= breakdown.taste_similarity <= 1.0
    assert 0.0 <= breakdown.compatibility_score <= 1.0
    assert len(breakdown.reason_chips) > 0
    # Verified grounded chips
    assert any("Harmony" in chip or "Top Pick" in chip for chip in breakdown.reason_chips)

    # Fallback embedding produces valid non-empty vector
    fallback = fallback_text_embedding("Oxford Shirt", "tops", "formal_shirts")
    assert isinstance(fallback, list)
    assert len(fallback) > 0
