from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from database.models import Base
from database.models.catalog import CanonicalGarment, StyleQuizPick
from database.models.identity import ConsentRecord, User
from database.models.tryon import TryOnJob
from fashx.application.erasure import ACCOUNT_TABLES, erase_account
from fashx.catalog.customer_router import _resolve_garment_detail
from fashx.catalog.repositories.catalog_repository import CatalogUnitOfWork
from fashx.core.errors import ValidationError
from fashx.profile.repositories.profile_repository import ProfileUnitOfWork
from fashx.profile.router import SubmitConsentRequest, submit_user_consent
from fashx.security.deps import Principal
from fashx.tryon.repositories.tryon_repository import TryOnUnitOfWork


@pytest_asyncio.fixture
async def session_factory() -> async_sessionmaker[AsyncSession]:
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    yield factory
    await engine.dispose()


@pytest.mark.asyncio
async def test_consent_records_contract_and_boundaries(session_factory) -> None:
    uow = ProfileUnitOfWork(session_factory)
    user_id = uuid4()
    principal = Principal(
        user_id=str(user_id),
        subject=str(user_id),
        roles=frozenset({"customer"}),
    )

    async with uow:
        uow.users.add(User(id=user_id))
        await uow.commit()

    # 1. Validation error if age_confirmed is False
    with pytest.raises(ValidationError, match="Age confirmation is required"):
        await submit_user_consent(
            user_id=user_id,
            req=SubmitConsentRequest(policy_version="2026.1", age_confirmed=False),
            principal=principal,
            profile_uow=uow,
        )

    # 2. Validation error if under 18 without parental consent
    with pytest.raises(ValidationError, match="Parental consent is required"):
        await submit_user_consent(
            user_id=user_id,
            req=SubmitConsentRequest(
                policy_version="2026.1",
                age_confirmed=True,
                age=16,
                parental_consent=False,
            ),
            principal=principal,
            profile_uow=uow,
        )

    # 3. Validation error if under 18 with invalid guardian email
    with pytest.raises(ValidationError, match="guardian email"):
        await submit_user_consent(
            user_id=user_id,
            req=SubmitConsentRequest(
                policy_version="2026.1",
                age_confirmed=True,
                age=16,
                parental_consent=True,
                guardian_email="bad-email",
            ),
            principal=principal,
            profile_uow=uow,
        )

    # 4. Under 18 with valid parental consent and guardian email succeeds
    resp_minor = await submit_user_consent(
        user_id=user_id,
        req=SubmitConsentRequest(
            policy_version="2026.1",
            age_confirmed=True,
            age=16,
            parental_consent=True,
            guardian_email="parent@example.com",
        ),
        principal=principal,
        profile_uow=uow,
    )
    assert resp_minor.status == "granted"
    assert resp_minor.policy_version == "2026.1"
    assert resp_minor.parental_consent is True
    assert resp_minor.guardian_email == "parent@example.com"

    # 5. Adult with valid age confirmed succeeds
    adult_id = uuid4()
    adult_principal = Principal(
        user_id=str(adult_id),
        subject=str(adult_id),
        roles=frozenset({"customer"}),
    )
    async with uow:
        uow.users.add(User(id=adult_id))
        await uow.commit()

    resp_adult = await submit_user_consent(
        user_id=adult_id,
        req=SubmitConsentRequest(
            policy_version="2026.1",
            age_confirmed=True,
            age=24,
        ),
        principal=adult_principal,
        profile_uow=uow,
    )
    assert resp_adult.status == "granted"
    assert resp_adult.policy_version == "2026.1"
    assert resp_adult.parental_consent is False


@pytest.mark.asyncio
async def test_style_quiz_picks_contract(session_factory) -> None:
    uow = CatalogUnitOfWork(session_factory)
    user_id = uuid4()
    garment_a = uuid4()
    garment_b = uuid4()

    async with uow:
        uow.canonical_garments.add(
            CanonicalGarment(id=garment_a, category="tops", subcategory="shirts")
        )
        uow.canonical_garments.add(
            CanonicalGarment(id=garment_b, category="bottoms", subcategory="trousers")
        )
        await uow.commit()

    async with uow:
        await uow.style_quiz_picks.upsert_pick(user_id, garment_a, liked=True)
        await uow.style_quiz_picks.upsert_pick(user_id, garment_b, liked=False)
        await uow.commit()

    async with uow:
        picks = await uow.style_quiz_picks.list_for_user(user_id)
        assert len(picks) == 2
        pick_map = {p.garment_id: p.liked for p in picks}
        assert pick_map[garment_a] is True
        assert pick_map[garment_b] is False

        count = await uow.style_quiz_picks.count_for_user(user_id)
        assert count == 2

        # Updating existing pick flips the boolean without duplicates
        await uow.style_quiz_picks.upsert_pick(user_id, garment_a, liked=False)
        await uow.commit()

    async with uow:
        count = await uow.style_quiz_picks.count_for_user(user_id)
        assert count == 2
        picks = await uow.style_quiz_picks.list_for_user(user_id)
        pick_map = {p.garment_id: p.liked for p in picks}
        assert pick_map[garment_a] is False


@pytest.mark.asyncio
async def test_customer_garment_detail_contract(session_factory) -> None:
    uow = CatalogUnitOfWork(session_factory)
    garment_id = uuid4()

    async with uow:
        uow.canonical_garments.add(
            CanonicalGarment(
                id=garment_id,
                display_name="Indigo Selvedge Denim Jacket",
                category="outerwear",
                subcategory="jackets",
                gender="unisex",
                price_minor=349900,
                sizes_in_stock=["M", "L", "XL"],
                tryon_supported=True,
            )
        )
        await uow.commit()

    detail = await _resolve_garment_detail(garment_id, uow)
    assert detail.id == garment_id
    assert detail.title == "Indigo Selvedge Denim Jacket"
    assert detail.category == "outerwear"
    assert detail.subcategory == "jackets"
    assert detail.price_minor == 349900
    assert detail.sizes_in_stock == ["M", "L", "XL"]
    assert detail.tryon_supported is True


@pytest.mark.asyncio
async def test_tryon_jobs_contract_and_user_history(session_factory) -> None:
    uow = TryOnUnitOfWork(session_factory)
    user_id = uuid4()
    job_1 = uuid4()
    job_2 = uuid4()
    garment_id = uuid4()
    photo_id = uuid4()

    async with uow:
        uow.jobs.add(
            TryOnJob(
                id=job_1,
                user_id=user_id,
                garment_id=garment_id,
                profile_photo_id=photo_id,
                idempotency_key="idemp_1",
                artifact_key="render_key_1",
                status="completed",
                model_version="fashx-vton-1.2",
                pipeline_version="p1",
                created_at=datetime(2026, 10, 15, 10, 0, tzinfo=UTC),
            )
        )
        uow.jobs.add(
            TryOnJob(
                id=job_2,
                user_id=user_id,
                garment_id=garment_id,
                profile_photo_id=photo_id,
                idempotency_key="idemp_2",
                artifact_key="render_key_2",
                status="queued",
                model_version="fashx-vton-1.2",
                pipeline_version="p1",
                created_at=datetime(2026, 10, 15, 11, 0, tzinfo=UTC),
            )
        )
        await uow.commit()

    async with uow:
        user_jobs = await uow.jobs.list_by_user(user_id)
        assert len(user_jobs) == 2
        # Verify ordered newest first
        assert user_jobs[0].id == job_2
        assert user_jobs[1].id == job_1


@pytest.mark.asyncio
async def test_erasure_covers_style_quiz_picks_and_consent(session_factory) -> None:
    assert "style_quiz_picks" in ACCOUNT_TABLES
    assert "consent_records" in ACCOUNT_TABLES

    user_id = uuid4()
    garment_id = uuid4()

    async with session_factory() as session:
        session.add(User(id=user_id))
        session.add(
            CanonicalGarment(
                id=garment_id,
                category="tops",
                gender="unisex",
            )
        )
        session.add(
            StyleQuizPick(
                id=uuid4(),
                user_id=user_id,
                garment_id=garment_id,
                liked=True,
            )
        )
        session.add(
            ConsentRecord(
                user_id=user_id,
                data_type="terms_and_privacy",
                granted=True,
                policy_version="2026.1",
            )
        )
        await session.commit()

    uow = ProfileUnitOfWork(session_factory)
    async with uow:
        await erase_account(uow, user_id)
        await uow.commit()

    async with session_factory() as session:
        res_pick = await session.execute(
            select(StyleQuizPick).where(StyleQuizPick.user_id == user_id)
        )
        assert res_pick.scalars().first() is None

        res_consent = await session.execute(
            select(ConsentRecord).where(ConsentRecord.user_id == user_id)
        )
        assert res_consent.scalars().first() is None
