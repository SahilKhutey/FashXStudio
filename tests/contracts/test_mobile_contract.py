from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
import pytest_asyncio
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from database.models import Base
from database.models.catalog import CanonicalGarment, StyleQuizPick
from database.models.identity import ConsentRecord, User, UserPhoto
from database.models.profile import OnboardingProfile
from database.models.tryon import TryOnJob
from fashx.api.v1.me import get_me
from fashx.application.erasure import ACCOUNT_TABLES, erase_account, erase_biometrics
from fashx.catalog.customer_router import _resolve_garment_detail
from fashx.catalog.repositories.catalog_repository import CatalogUnitOfWork
from fashx.core.errors import ConsentRequiredError, EntityNotFoundError
from fashx.profile.application.upload_photo import UploadPhotoCommand, UploadUserPhotoUseCase
from fashx.profile.repositories.profile_repository import ProfileUnitOfWork
from fashx.profile.router import ConsentGrantIn, submit_user_consent
from fashx.security.deps import Principal
from fashx.security.errors import ApiError
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
    """Consent grant: adults only. Under 18 gets 403 and nothing is stored. Extra fields return 422."""
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

    # 1. Under-18 is strictly rejected with 403 (age_requirement) and zero records stored
    with pytest.raises(ApiError) as exc_info:
        await submit_user_consent(
            user_id=user_id,
            req=ConsentGrantIn(
                consent_version="2026.1",
                is_18_or_older=False,
                accepts_terms=True,
                accepts_body_photo=True,
            ),
            principal=principal,
            profile_uow=uow,
        )
    assert exc_info.value.status == 403
    assert exc_info.value.code == "age_requirement"
    assert "18 or older" in exc_info.value.detail

    async with uow:
        stored_consents = await uow.consents.list_for_user(user_id)
        assert len(stored_consents) == 0, "No consent records must be stored when age verification fails"

    # 2. Outdated consent_version is rejected with 409 (consent_version_outdated)
    with pytest.raises(ApiError) as ver_err:
        await submit_user_consent(
            user_id=user_id,
            req=ConsentGrantIn(
                consent_version="2025.1",
                is_18_or_older=True,
                accepts_terms=True,
                accepts_body_photo=True,
            ),
            principal=principal,
            profile_uow=uow,
        )
    assert ver_err.value.status == 409
    assert ver_err.value.code == "consent_version_outdated"

    # 3. Unbundled consent: accepts_terms=False is rejected with 400 (terms_required)
    with pytest.raises(ApiError) as terms_err:
        await submit_user_consent(
            user_id=user_id,
            req=ConsentGrantIn(
                consent_version="2026.1",
                is_18_or_older=True,
                accepts_terms=False,
                accepts_body_photo=True,
            ),
            principal=principal,
            profile_uow=uow,
        )
    assert terms_err.value.status == 400
    assert terms_err.value.code == "terms_required"

    # 4. Unbundled consent: accepts_body_photo=False is rejected with 400 (body_photo_consent_required)
    with pytest.raises(ApiError) as photo_err:
        await submit_user_consent(
            user_id=user_id,
            req=ConsentGrantIn(
                consent_version="2026.1",
                is_18_or_older=True,
                accepts_terms=True,
                accepts_body_photo=False,
            ),
            principal=principal,
            profile_uow=uow,
        )
    assert photo_err.value.status == 400
    assert photo_err.value.code == "body_photo_consent_required"

    # 5. Pydantic validation rejects extra fields (e.g. guardian_email or legacy fields)
    with pytest.raises(PydanticValidationError) as val_err:
        ConsentGrantIn.model_validate(
            {
                "consent_version": "2026.1",
                "is_18_or_older": True,
                "accepts_terms": True,
                "accepts_body_photo": True,
                "guardian_email": "parent@example.com",
            }
        )
    assert "extra_forbidden" in str(val_err.value)

    # 6. Cross-user protection: principal mismatch raises 403 forbidden
    other_user_id = uuid4()
    with pytest.raises(ApiError) as cross_err:
        await submit_user_consent(
            user_id=other_user_id,
            req=ConsentGrantIn(
                consent_version="2026.1",
                is_18_or_older=True,
                accepts_terms=True,
                accepts_body_photo=True,
            ),
            principal=principal,
            profile_uow=uow,
        )
    assert cross_err.value.status == 403

    # 7. Valid adult consent succeeds and grants both terms_and_privacy and body_photo with independent records
    resp = await submit_user_consent(
        user_id=user_id,
        req=ConsentGrantIn(
            consent_version="2026.1",
            is_18_or_older=True,
            accepts_terms=True,
            accepts_body_photo=True,
        ),
        principal=principal,
        profile_uow=uow,
    )
    assert resp.status == "granted"
    assert resp.consent_version == "2026.1"
    assert resp.is_18_or_older is True
    assert resp.accepts_terms is True
    assert resp.accepts_body_photo is True

    async with uow:
        assert await uow.consents.has_consent(user_id, "terms_and_privacy")
        assert await uow.consents.has_consent(user_id, "body_photo")
        user_consents = await uow.consents.list_for_user(user_id)
        assert len(user_consents) == 2
        terms_rec = next(c for c in user_consents if c.data_type == "terms_and_privacy")
        photo_rec = next(c for c in user_consents if c.data_type == "body_photo")
        assert terms_rec.granted is True
        assert photo_rec.granted is True
        assert terms_rec.consent_version == "2026.1"
        assert photo_rec.consent_version == "2026.1"


@pytest.mark.asyncio
async def test_photo_upload_refuses_without_active_consent(session_factory) -> None:
    """Photo upload must refuse with ConsentRequiredError (HTTP 403) without consent or after revoke."""
    uow = ProfileUnitOfWork(session_factory)
    user_id = uuid4()

    async with uow:
        uow.users.add(User(id=user_id))
        await uow.commit()

    use_case = UploadUserPhotoUseCase(uow)
    cmd = UploadPhotoCommand(
        user_id=user_id,
        photo_type="body",
        photo_bytes=b"dummy_raw_photo_bytes",
    )

    # 1. Without active consent: raises ConsentRequiredError
    with pytest.raises(ConsentRequiredError) as exc_info:
        await use_case.execute(cmd)
    assert exc_info.value.code == "consent_required"
    assert "body_photo" in str(exc_info.value.message)

    # 2. After granting mobile consent: consent check passes
    async with uow:
        await uow.consents.record_mobile_consent(
            user_id=user_id,
            consent_version="2026.1",
            is_18_or_older=True,
            accepts_terms=True,
            accepts_body_photo=True,
        )
        await uow.commit()

    # Consent check passes; fails at downstream quality validator
    try:
        await use_case.execute(cmd)
    except ConsentRequiredError:
        pytest.fail("UploadUserPhotoUseCase should not raise ConsentRequiredError after consent is granted")
    except Exception:
        pass

    # 3. After consent revocation (via erase_biometrics): upload is refused again with 403 consent_required
    async with uow:
        await erase_biometrics(uow, user_id, record_revocation=True)
        await uow.commit()

    with pytest.raises(ConsentRequiredError) as revoked_err:
        await use_case.execute(cmd)
    assert revoked_err.value.code == "consent_required"


@pytest.mark.asyncio
async def test_onboarding_missing_order_table_driven(session_factory) -> None:
    """Table-driven test verifying onboarding.missing strictly adheres to [consent, profile, style_quiz, photo]."""
    test_cases = [
        # (has_consent, has_profile, has_quiz, has_photo, expected_missing, expected_complete)
        (False, False, False, False, ["consent", "profile", "style_quiz", "photo"], False),
        (True, False, False, False, ["profile", "style_quiz", "photo"], False),
        (True, True, False, False, ["style_quiz", "photo"], False),
        (True, True, True, False, ["photo"], False),
        (True, True, True, True, [], True),
    ]

    for has_c, has_p, has_q, has_ph, expected_missing, expected_complete in test_cases:
        uow = ProfileUnitOfWork(session_factory)
        user_id = uuid4()
        principal = Principal(user_id=str(user_id), subject=str(user_id), roles=frozenset({"customer"}))

        async with uow:
            uow.users.add(User(id=user_id))
            if has_c:
                uow.consents.add(
                    ConsentRecord(
                        user_id=user_id,
                        data_type="terms_and_privacy",
                        granted=True,
                        consent_version="2026.1",
                        is_18_or_older=True,
                    )
                )
            if has_p:
                uow.onboarding_profiles.add(
                    OnboardingProfile(user_id=user_id, status="completed")
                )
            if has_q:
                garment_id = uuid4()
                uow.session.add(
                    CanonicalGarment(id=garment_id, category="tops", gender="unisex")
                )
                uow.session.add(
                    StyleQuizPick(id=uuid4(), user_id=user_id, garment_id=garment_id, liked=True)
                )
            if has_ph:
                uow.photos.add(
                    UserPhoto(
                        id=uuid4(),
                        user_id=user_id,
                        photo_type="body",
                        storage_key=f"u/{user_id}/photos/1.jpg",
                        status="accepted",
                    )
                )
            await uow.commit()

        me_resp = await get_me(principal=principal, profile_uow=uow)
        assert me_resp.onboarding.missing == expected_missing, (
            f"Failed on case {(has_c, has_p, has_q, has_ph)}: expected {expected_missing}, got {me_resp.onboarding.missing}"
        )
        assert me_resp.onboarding.complete == expected_complete


@pytest.mark.asyncio
async def test_style_quiz_picks_contract(session_factory) -> None:
    uow = CatalogUnitOfWork(session_factory)
    user_id = uuid4()
    other_user_id = uuid4()
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
        await uow.style_quiz_picks.upsert_pick(other_user_id, garment_a, liked=False)
        await uow.commit()

    async with uow:
        picks = await uow.style_quiz_picks.list_for_user(user_id)
        assert len(picks) == 2
        pick_map = {p.garment_id: p.liked for p in picks}
        assert pick_map[garment_a] is True
        assert pick_map[garment_b] is False

        # Cross-user isolation: user_id sees only their picks
        other_picks = await uow.style_quiz_picks.list_for_user(other_user_id)
        assert len(other_picks) == 1
        assert other_picks[0].liked is False

        # Flipping pick without duplicate
        await uow.style_quiz_picks.upsert_pick(user_id, garment_a, liked=False)
        await uow.commit()

    async with uow:
        assert await uow.style_quiz_picks.count_for_user(user_id) == 2
        picks = await uow.style_quiz_picks.list_for_user(user_id)
        assert {p.garment_id: p.liked for p in picks}[garment_a] is False


@pytest.mark.asyncio
async def test_customer_garment_detail_contract(session_factory) -> None:
    uow = CatalogUnitOfWork(session_factory)
    garment_id = uuid4()
    inactive_id = uuid4()

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
                active=True,
            )
        )
        uow.canonical_garments.add(
            CanonicalGarment(
                id=inactive_id,
                display_name="Deprecated Garment",
                category="outerwear",
                gender="unisex",
                active=False,
            )
        )
        await uow.commit()

    # 1. Active garment returns detail with extra=forbid model
    detail = await _resolve_garment_detail(garment_id, uow)
    assert detail.id == garment_id
    assert detail.title == "Indigo Selvedge Denim Jacket"
    assert detail.category == "outerwear"
    assert detail.subcategory == "jackets"
    assert detail.price_minor == 349900
    assert detail.sizes_in_stock == ["M", "L", "XL"]
    assert detail.tryon_supported is True

    # 2. Inactive garment raises EntityNotFoundError (404)
    with pytest.raises(EntityNotFoundError):
        await _resolve_garment_detail(inactive_id, uow)

    # 3. Nonexistent garment raises EntityNotFoundError (404)
    with pytest.raises(EntityNotFoundError):
        await _resolve_garment_detail(uuid4(), uow)


@pytest.mark.asyncio
async def test_tryon_jobs_contract_and_user_history(session_factory) -> None:
    uow = TryOnUnitOfWork(session_factory)
    user_id = uuid4()
    other_user_id = uuid4()
    job_1 = uuid4()
    job_2 = uuid4()
    job_other = uuid4()
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
        uow.jobs.add(
            TryOnJob(
                id=job_other,
                user_id=other_user_id,
                garment_id=garment_id,
                profile_photo_id=photo_id,
                idempotency_key="idemp_3",
                artifact_key="render_key_3",
                status="completed",
                model_version="fashx-vton-1.2",
                pipeline_version="p1",
                created_at=datetime(2026, 10, 15, 12, 0, tzinfo=UTC),
            )
        )
        await uow.commit()

    async with uow:
        user_jobs = await uow.jobs.list_by_user(user_id)
        assert len(user_jobs) == 2
        # Verify ordered newest first
        assert user_jobs[0].id == job_2
        assert user_jobs[1].id == job_1

        # Cross-user isolation: user cannot see other's jobs
        other_jobs = await uow.jobs.list_by_user(other_user_id)
        assert len(other_jobs) == 1
        assert other_jobs[0].id == job_other


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
                consent_version="2026.1",
                is_18_or_older=True,
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


@pytest.mark.asyncio
async def test_garment_tryon_eligibility_hotlink_source_is_false() -> None:
    """Verify that garments from hotlink-only sources fail closed (tryon_supported = False)."""
    from fashx.catalog.eligibility import compute_tryon_eligibility

    # 1. Hotlink image policy must compute False even if rights_tryon is claimed
    hotlink_res = compute_tryon_eligibility(
        source_rights_tryon=True,
        source_image_policy="hotlink",
        vlm_tryon_suitable=True,
        vlm_confidence=0.95,
        category="tops",
    )
    assert hotlink_res is False

    # 2. Source without rights_tryon must compute False
    no_rights_res = compute_tryon_eligibility(
        source_rights_tryon=False,
        source_image_policy="mirror",
        vlm_tryon_suitable=True,
        vlm_confidence=0.95,
        category="tops",
    )
    assert no_rights_res is False

    # 3. Mirrored partner source with rights_tryon computes True
    cleared_res = compute_tryon_eligibility(
        source_rights_tryon=True,
        source_image_policy="mirror",
        vlm_tryon_suitable=True,
        vlm_confidence=0.95,
        category="tops",
    )
    assert cleared_res is True


def test_consent_endpoint_http_level(session_factory) -> None:
    """HTTP-level contract test for POST /profile/{user_id}/consent verifying auth and version boundaries."""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from fashx.profile.router import get_profile_uow
    from fashx.profile.router import router as profile_router
    from fashx.security.deps import get_identity_repo
    from fashx.security.errors import api_error_handler
    from fashx.security.identity import InMemoryIdentityRepo
    from tests.conftest import make_token

    app = FastAPI()
    app.add_exception_handler(ApiError, api_error_handler)
    repo = InMemoryIdentityRepo()
    app.dependency_overrides[get_identity_repo] = lambda: repo
    app.dependency_overrides[get_profile_uow] = lambda: ProfileUnitOfWork(session_factory)

    # profile_router has prefix="/profile", so mounting under /api/v1 exposes /api/v1/profile/{user_id}/consent
    app.include_router(profile_router, prefix="/api/v1")
    client = TestClient(app)

    import asyncio

    identity_a = asyncio.run(repo.resolve("fashx-test", "user-a"))
    user_a = identity_a.user_id
    user_b = str(uuid4())
    token_a = make_token(sub="user-a")

    payload = {
        "consent_version": "2026.1",
        "is_18_or_older": True,
        "accepts_terms": True,
        "accepts_body_photo": True,
    }

    # 1. Unauthenticated request returns 401
    resp_no_auth = client.post(f"/api/v1/profile/{user_a}/consent", json=payload, headers={"Authorization": ""})
    assert resp_no_auth.status_code == 401

    # 2. Authenticated request for a different user returns 403
    resp_cross = client.post(
        f"/api/v1/profile/{user_b}/consent",
        json=payload,
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert resp_cross.status_code == 403

    # 3. Outdated consent_version returns 409
    outdated_payload = {**payload, "consent_version": "2025.1"}
    resp_outdated = client.post(
        f"/api/v1/profile/{user_a}/consent",
        json=outdated_payload,
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert resp_outdated.status_code == 409

    # 4. Under 18 returns 403
    under18_payload = {**payload, "is_18_or_older": False}
    resp_under18 = client.post(
        f"/api/v1/profile/{user_a}/consent",
        json=under18_payload,
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert resp_under18.status_code == 403

    # 5. Missing accepts_terms returns 400
    no_terms_payload = {**payload, "accepts_terms": False}
    resp_no_terms = client.post(
        f"/api/v1/profile/{user_a}/consent",
        json=no_terms_payload,
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert resp_no_terms.status_code == 400

    # 6. Valid request returns 201
    resp_valid = client.post(
        f"/api/v1/profile/{user_a}/consent",
        json=payload,
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert resp_valid.status_code == 201
    data = resp_valid.json()
    assert data["status"] == "granted"
    assert data["consent_version"] == "2026.1"
    assert data["is_18_or_older"] is True
    assert data["accepts_terms"] is True
    assert data["accepts_body_photo"] is True


@pytest.mark.asyncio
async def test_erasure_injected_failure_rolls_back(session_factory) -> None:
    """Verify that if an error occurs during erasure, the entire transaction rolls back and raises ErasureIncomplete."""
    from fashx.application.erasure import ErasureIncomplete, erase_account

    user_id = uuid4()
    async with session_factory() as session:
        session.add(User(id=user_id))
        session.add(
            ConsentRecord(
                user_id=user_id,
                data_type="terms_and_privacy",
                granted=True,
                consent_version="2026.1",
                is_18_or_older=True,
            )
        )
        await session.commit()

    uow = ProfileUnitOfWork(session_factory)
    async with uow:
        orig_execute = uow.session.execute

        async def faulty_execute(statement, *args, **kwargs):
            if 'DELETE FROM "users"' in str(statement):
                raise RuntimeError("Injected database failure during users delete")
            return await orig_execute(statement, *args, **kwargs)

        uow.session.execute = faulty_execute

        with pytest.raises(ErasureIncomplete) as exc_info:
            await erase_account(uow, user_id)
        assert "RuntimeError" in str(exc_info.value)

    # Verify no partial deletion: user and consent records still exist because of rollback
    async with session_factory() as session:
        user_row = await session.get(User, user_id)
        assert user_row is not None, "User row must not be deleted when erasure fails"
        consent_row = await session.get(ConsentRecord, (user_id, "terms_and_privacy"))
        assert consent_row is not None, "Consent record must not be deleted when erasure fails"

