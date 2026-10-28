from datetime import UTC, datetime
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from database.models.commerce_feedback import DomainEvent
from database.models.identity import User
from database.models.tryon import TryOnJob
from fashx.catalog.embeddings.ports import validate_embedding_vector
from fashx.discovery.taste import SignalEvent, compute_taste_vector
from fashx.main import app as main_app
from fashx.recommendation.compatibility import CompatibilityScore
from fashx.recommendation.filters import CandidateItem
from fashx.recommendation.ranker import cosine_similarity
from fashx.recommendation.scoring import compute_explainable_score
from fashx.security.deps import Principal, get_principal
from fashx.tryon.application.process_job import ProcessTryOnJobUseCase
from fashx.tryon.repositories.tryon_repository import TryOnUnitOfWork


def test_missing_embedding_is_not_neutral_similarity() -> None:
    """Missing vectors must return None, not an artificial neutral 0.5."""
    assert cosine_similarity([1.0, 0.0], None) is None
    assert cosine_similarity(None, [1.0, 0.0]) is None
    assert cosine_similarity(None, None) is None


def test_zero_norm_embedding_is_not_comparable() -> None:
    """Zero-norm vectors cannot be normalized and must return None."""
    assert cosine_similarity([0.0, 0.0], [1.0, 0.0]) is None
    assert cosine_similarity([1.0, 0.0], [0.0, 0.0]) is None
    assert cosine_similarity([0.0, 0.0], [0.0, 0.0]) is None


def test_dimension_mismatch_is_not_comparable() -> None:
    """Vectors of different dimensions cannot be compared in cosine space."""
    assert cosine_similarity([1.0, 0.0], [1.0]) is None
    assert cosine_similarity([1.0, 0.0, 0.0], [1.0, 0.0]) is None


def test_vector_validation_enforces_dimensions_finite_values_and_norm() -> None:
    """Vector validator enforces 512 dimensions, finite values, and non-zero norm."""
    valid_vec = [1.0 / (512**0.5)] * 512
    validate_embedding_vector(valid_vec, expected_dim=512)

    with pytest.raises(ValueError, match="dimension mismatch"):
        validate_embedding_vector([1.0, 2.0], expected_dim=512)

    with pytest.raises(ValueError, match="non-finite"):
        nan_vec = list(valid_vec)
        nan_vec[0] = float("nan")
        validate_embedding_vector(nan_vec, expected_dim=512)

    with pytest.raises(ValueError, match="zero norm"):
        validate_embedding_vector([0.0] * 512, expected_dim=512)


def test_explainable_scoring_dynamic_reweighting_omits_missing_similarity() -> None:
    """When taste similarity is missing, scoring renormalizes over available components without 0.5 bias."""
    cand = CandidateItem(
        garment_id=uuid4(),
        category="tops",
        subcategory="tshirts",
        price_minor=199900,
        in_stock=True,
        dominant_color="navy",
        silhouette="straight",
        embedding=None,  # Missing embedding
    )
    compat = CompatibilityScore(
        color_score=0.90,
        silhouette_score=0.80,
        total_score=0.85,
        color_reason="Complementary navy",
        silhouette_reason="Standard straight cut",
    )

    # 1. Without taste signal -> relevance is exactly compatibility score (0.85)
    breakdown_no_signal = compute_explainable_score(
        item=cand,
        compatibility=compat,
        taste_vector=None,
        has_taste_signal=False,
    )
    assert breakdown_no_signal.taste_similarity is None
    assert breakdown_no_signal.relevance_score == 0.85
    assert breakdown_no_signal.feature_contributions["taste_similarity"] == 0.0
    assert breakdown_no_signal.feature_contributions["compatibility"] == 0.85

    # 2. With valid taste vector and valid embedding -> weighted average
    valid_vec = [1.0 / (512**0.5)] * 512
    cand_with_emb = CandidateItem(
        garment_id=uuid4(),
        category="tops",
        subcategory="tshirts",
        price_minor=199900,
        in_stock=True,
        dominant_color="navy",
        silhouette="straight",
        embedding=valid_vec,
    )
    breakdown_with_emb = compute_explainable_score(
        item=cand_with_emb,
        compatibility=compat,
        taste_vector=valid_vec,
        has_taste_signal=True,
        weight_taste=0.5,
        weight_compat=0.5,
    )
    assert breakdown_with_emb.taste_similarity is not None
    assert pytest.approx(breakdown_with_emb.taste_similarity, abs=1e-3) == 1.0
    # Average of 1.0 (taste) and 0.85 (compat) = 0.925
    assert breakdown_with_emb.relevance_score == 0.925
    assert "Style Match" in breakdown_with_emb.reason_chips


def test_taste_vector_steers_with_positive_and_negative_signals() -> None:
    """Taste vector updates appropriately with like vs hide signals."""
    now = datetime.now(UTC)
    vec_a = [1.0 / (512**0.5)] * 512
    vec_b = [-1.0 / (512**0.5)] * 512

    # Taste with ethnic archetype
    taste_archetype = compute_taste_vector([], user_styles=["ethnic"], now=now)
    assert len(taste_archetype) == 512

    # Taste with positive like signals
    sig_like = [
        SignalEvent(
            garment_id=str(uuid4()),
            action="like",
            timestamp=now,
            embedding=taste_archetype,
        )
    ]
    taste_liked = compute_taste_vector(sig_like, user_styles=["ethnic"], now=now)
    assert len(taste_liked) == 512

    # Taste with negative signals
    sig_hide = [
        SignalEvent(
            garment_id=str(uuid4()),
            action="hide",
            timestamp=now,
            embedding=taste_archetype,
        )
    ]
    taste_hidden = compute_taste_vector(sig_hide, user_styles=["ethnic"], now=now)
    assert not (taste_liked == taste_hidden).all()


@pytest.mark.asyncio
async def test_process_job_fails_closed_on_corrupt_photo_bytes(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Try-on worker rejects unparseable or corrupt photo bytes with typed failure."""
    from database.models.catalog import CanonicalGarment
    from fashx.catalog.repositories.catalog_repository import CatalogUnitOfWork
    from fashx.profile.repositories.profile_repository import ProfileUnitOfWork

    tryon_uow = TryOnUnitOfWork(session_factory)
    profile_uow = ProfileUnitOfWork(session_factory)
    catalog_uow = CatalogUnitOfWork(session_factory)

    user_id = uuid4()
    job_id = uuid4()
    garment_id = uuid4()
    photo_id = uuid4()

    async with profile_uow:
        profile_uow.users.add(User(id=user_id))
        await profile_uow.consents.upsert(user_id=user_id, data_type="body_photo", granted=True)
        await profile_uow.commit()

    async with catalog_uow:
        garment = CanonicalGarment(
            id=garment_id,
            display_name="Oxford Shirt",
            category="tops",
            subcategory="shirts",
            gender="unisex",
            active=True,
            in_stock=True,
            price_minor=450000,
            tryon_supported=True,
            version=1,
        )
        catalog_uow.canonical_garments.add(garment)
        await catalog_uow.commit()

    async with tryon_uow:
        job = TryOnJob(
            id=job_id,
            user_id=user_id,
            garment_id=garment_id,
            profile_photo_id=photo_id,
            idempotency_key=f"idemp-{job_id}",
            artifact_key=f"users/{user_id}/tryon/{job_id}.png",
            status="pending",
            model_version="tryon-v1.6",
            pipeline_version="pilot-pipe-v1",
        )
        tryon_uow.jobs.add(job)
        await tryon_uow.commit()

    use_case = ProcessTryOnJobUseCase(
        tryon_uow=tryon_uow,
        profile_uow=profile_uow,
        catalog_uow=catalog_uow,
    )

    # Pass corrupt bytes
    corrupt_bytes = b"not_a_valid_image_header_bytes_12345"
    res = await use_case.execute(
        job_id=job_id,
        user_photo_bytes=corrupt_bytes,
        garment_image_bytes=corrupt_bytes,
    )
    assert res.status == "failed"
    assert "invalid_photo_bytes" in (res.failure_reason or "")

    async with tryon_uow:
        updated_job = await tryon_uow.jobs.get_by_id(job_id)
        assert updated_job is not None
        assert updated_job.status == "failed"


@pytest.mark.asyncio
async def test_analytics_journey_events_idempotent_deduplication() -> None:
    """Product journey events enforce exact-once deduplication under network retry."""
    from fashx.api.v1.analytics import get_analytics_session_factory

    app_session_factory = main_app.dependency_overrides[get_analytics_session_factory]()
    user_id = uuid4()
    event_id = uuid4()
    garment_id = uuid4()

    async with app_session_factory() as session:
        session.add(User(id=user_id))
        await session.commit()

    try:
        main_app.dependency_overrides[get_principal] = lambda: Principal(
            user_id=str(user_id),
            subject=str(user_id),
            roles=frozenset(["user"]),
        )

        transport = ASGITransport(app=main_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            payload = {
                "events": [
                    {
                        "event_id": str(event_id),
                        "event_name": "garment_opened",
                        "occurred_at": datetime.now(UTC).isoformat(),
                        "garment_id": str(garment_id),
                        "tryon_job_id": None,
                        "schema_version": 1,
                    }
                ]
            }

            # First request -> recorded: 1, duplicates_skipped: 0
            resp1 = await client.post("/api/v1/analytics/journey-events", json=payload)
            assert resp1.status_code == 201
            data1 = resp1.json()
            assert data1["status"] == "recorded"
            assert data1["count"] == 1
            assert data1["duplicates_skipped"] == 0

            # Duplicate retry -> recorded: 0, duplicates_skipped: 1
            resp2 = await client.post("/api/v1/analytics/journey-events", json=payload)
            assert resp2.status_code == 201
            data2 = resp2.json()
            assert data2["count"] == 0
            assert data2["duplicates_skipped"] == 1

            # Verify exactly one record in the database
            async with app_session_factory() as session:
                ev = await session.get(DomainEvent, event_id)
                assert ev is not None
                assert ev.event_type == "journey_garment_opened"
                assert ev.user_id == user_id
    finally:
        main_app.dependency_overrides.pop(get_principal, None)
