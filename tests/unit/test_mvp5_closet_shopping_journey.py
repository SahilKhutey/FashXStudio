from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from database.models.catalog import (
    CanonicalGarment,
    Merchant,
    MerchantOffer,
)
from database.models.identity import User
from database.models.tryon import TryOnArtifact, TryOnJob
from fashx.catalog.repositories.catalog_repository import CatalogUnitOfWork
from fashx.commerce_wardrobe.application.create_buy_click import (
    CreateBuyClickCommand,
    CreateBuyClickUseCase,
    validate_retailer_url,
)
from fashx.commerce_wardrobe.application.list_wardrobe import ListWardrobeUseCase
from fashx.commerce_wardrobe.application.save_to_wardrobe import (
    SaveToWardrobeCommand,
    SaveToWardrobeUseCase,
)
from fashx.commerce_wardrobe.repositories.commerce_wardrobe_repository import (
    CommerceWardrobeUnitOfWork,
)
from fashx.commerce_wardrobe.router import (
    get_catalog_uow,
    get_commerce_uow,
    get_profile_uow,
)
from fashx.commerce_wardrobe.router import (
    router as commerce_router,
)
from fashx.core.database import get_session_factory
from fashx.core.dependencies import get_storage
from fashx.core.errors import ValidationError
from fashx.gateway.errors import install_exception_handlers
from fashx.infrastructure.storage.local import LocalStorage
from fashx.profile.repositories.profile_repository import ProfileUnitOfWork
from fashx.security.deps import get_identity_repo
from fashx.security.errors import ApiError, api_error_handler
from fashx.security.identity import InMemoryIdentityRepo
from fashx.tryon.repositories.tryon_repository import TryOnUnitOfWork
from fashx.tryon.router import get_tryon_uow
from fashx.tryon.router import router as tryon_router
from tests.conftest import make_token


def create_test_client(
    session_factory: async_sessionmaker[AsyncSession],
    storage: Any | None = None,
) -> tuple[TestClient, InMemoryIdentityRepo]:
    app = FastAPI()
    app.add_exception_handler(ApiError, api_error_handler)
    install_exception_handlers(app)
    repo = InMemoryIdentityRepo()
    app.dependency_overrides[get_identity_repo] = lambda: repo
    app.dependency_overrides[get_commerce_uow] = lambda: CommerceWardrobeUnitOfWork(session_factory)
    app.dependency_overrides[get_profile_uow] = lambda: ProfileUnitOfWork(session_factory)
    app.dependency_overrides[get_catalog_uow] = lambda: CatalogUnitOfWork(session_factory)
    app.dependency_overrides[get_tryon_uow] = lambda: TryOnUnitOfWork(session_factory)
    app.dependency_overrides[get_session_factory] = lambda: session_factory
    if storage is not None:
        app.dependency_overrides[get_storage] = lambda: storage
    app.include_router(commerce_router)
    app.include_router(tryon_router)
    return TestClient(app), repo


@pytest.mark.asyncio
async def test_wardrobe_save_derives_user_from_principal(
    session_factory: async_sessionmaker[AsyncSession],
    tmp_path,
) -> None:
    """MVP 5.1: POST /wardrobe/items derives user identity strictly from the authenticated token."""
    storage = LocalStorage(tmp_path)
    client, repo = create_test_client(session_factory, storage)

    identity = await repo.resolve("fashx-test", "user-closet-1")
    user_id = UUID(identity.user_id)
    token = make_token(sub="user-closet-1")

    profile_uow = ProfileUnitOfWork(session_factory)
    catalog_uow = CatalogUnitOfWork(session_factory)

    async with profile_uow:
        profile_uow.users.add(User(id=user_id))
        await profile_uow.commit()

    garment_id = uuid4()
    async with catalog_uow:
        garment = CanonicalGarment(
            id=garment_id,
            display_name="Silk Shirt",
            category="tops",
            subcategory="blouses",
            gender="women",
            active=True,
            in_stock=True,
            price_minor=350000,
            tryon_supported=True,
            version=1,
        )
        catalog_uow.canonical_garments.add(garment)
        await catalog_uow.commit()

    # Client omits user_id from payload -> server derives user_id from token
    resp = client.post(
        "/wardrobe/items",
        json={"garment_id": str(garment_id)},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["user_id"] == str(user_id)
    assert data["garment_id"] == str(garment_id)
    assert "Silk Shirt" in data["snapshot_title"] or "Tops" in data["snapshot_title"]
    assert data["image_url"] is not None


@pytest.mark.asyncio
async def test_wardrobe_save_rejects_user_id_mismatch(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """MVP 5.1: POST /wardrobe/items with a mismatched user_id returns 403 forbidden."""
    client, repo = create_test_client(session_factory)

    await repo.resolve("fashx-test", "user-real")
    token = make_token(sub="user-real")
    fake_user_id = uuid4()

    resp = client.post(
        "/wardrobe/items",
        json={"user_id": str(fake_user_id), "garment_id": str(uuid4())},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403
    assert "forbidden" in resp.text.lower()


@pytest.mark.asyncio
async def test_wardrobe_save_idempotency_and_uniqueness(
    session_factory: async_sessionmaker[AsyncSession],
    tmp_path,
) -> None:
    """MVP 5.2: Saving the same garment twice updates snapshot without creating duplicate rows."""
    storage = LocalStorage(tmp_path)
    profile_uow = ProfileUnitOfWork(session_factory)
    catalog_uow = CatalogUnitOfWork(session_factory)
    wardrobe_uow = CommerceWardrobeUnitOfWork(session_factory)

    user_id = uuid4()
    garment_id = uuid4()

    async with profile_uow:
        profile_uow.users.add(User(id=user_id))
        await profile_uow.commit()

    async with catalog_uow:
        garment = CanonicalGarment(
            id=garment_id,
            display_name="Classic Navy Polo",
            category="tops",
            subcategory="polo",
            gender="men",
            active=True,
            in_stock=True,
            price_minor=250000,
            tryon_supported=True,
            version=1,
        )
        catalog_uow.canonical_garments.add(garment)
        await catalog_uow.commit()

    save_uc = SaveToWardrobeUseCase(wardrobe_uow, profile_uow, catalog_uow, storage=storage)

    # First save
    res1 = await save_uc.execute(SaveToWardrobeCommand(user_id=user_id, garment_id=garment_id))
    assert res1.item_id is not None

    # Second save (repeat request) -> returns same item_id
    res2 = await save_uc.execute(SaveToWardrobeCommand(user_id=user_id, garment_id=garment_id))
    assert res2.item_id == res1.item_id

    # Verify database table contains exactly 1 row
    list_uc = ListWardrobeUseCase(wardrobe_uow)
    items = await list_uc.execute(user_id)
    assert len(items) == 1


@pytest.mark.asyncio
async def test_list_my_wardrobe_endpoint(
    session_factory: async_sessionmaker[AsyncSession],
    tmp_path,
) -> None:
    """MVP 5.3: GET /wardrobe/items lists authenticated user's items with signed URLs."""
    storage = LocalStorage(tmp_path)
    client, repo = create_test_client(session_factory, storage)

    identity_a = await repo.resolve("fashx-test", "user-a-closet")
    user_a_id = UUID(identity_a.user_id)
    token_a = make_token(sub="user-a-closet")

    identity_b = await repo.resolve("fashx-test", "user-b-closet")
    token_b = make_token(sub="user-b-closet")

    profile_uow = ProfileUnitOfWork(session_factory)
    catalog_uow = CatalogUnitOfWork(session_factory)
    wardrobe_uow = CommerceWardrobeUnitOfWork(session_factory)

    async with profile_uow:
        profile_uow.users.add(User(id=user_a_id))
        await profile_uow.commit()

    garment_id = uuid4()
    async with catalog_uow:
        garment = CanonicalGarment(
            id=garment_id,
            display_name="Corduroy Jacket",
            category="outerwear",
            subcategory="jackets",
            gender="unisex",
            active=True,
            in_stock=True,
            price_minor=650000,
            tryon_supported=True,
            version=1,
        )
        catalog_uow.canonical_garments.add(garment)
        await catalog_uow.commit()

    save_uc = SaveToWardrobeUseCase(wardrobe_uow, profile_uow, catalog_uow, storage=storage)
    await save_uc.execute(SaveToWardrobeCommand(user_id=user_a_id, garment_id=garment_id))

    # User A requests their wardrobe
    resp_a = client.get("/wardrobe/items", headers={"Authorization": f"Bearer {token_a}"})
    assert resp_a.status_code == 200
    items_a = resp_a.json()
    assert len(items_a) == 1
    assert items_a[0]["garment_id"] == str(garment_id)
    assert items_a[0]["image_url"] is not None

    # User B requests their wardrobe -> empty list (isolation)
    resp_b = client.get("/wardrobe/items", headers={"Authorization": f"Bearer {token_b}"})
    assert resp_b.status_code == 200
    assert len(resp_b.json()) == 0


@pytest.mark.asyncio
async def test_remove_from_wardrobe_ownership_enforcement(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """MVP 5.4: User B cannot delete User A's wardrobe item (404/not found), only owner can delete."""
    client, repo = create_test_client(session_factory)

    identity_a = await repo.resolve("fashx-test", "user-owner")
    user_a_id = UUID(identity_a.user_id)
    token_a = make_token(sub="user-owner")

    await repo.resolve("fashx-test", "user-intruder")
    token_b = make_token(sub="user-intruder")

    profile_uow = ProfileUnitOfWork(session_factory)
    catalog_uow = CatalogUnitOfWork(session_factory)
    wardrobe_uow = CommerceWardrobeUnitOfWork(session_factory)

    async with profile_uow:
        profile_uow.users.add(User(id=user_a_id))
        await profile_uow.commit()

    garment_id = uuid4()
    async with catalog_uow:
        garment = CanonicalGarment(
            id=garment_id,
            display_name="Denim Overshirt",
            category="tops",
            subcategory="shirts",
            gender="men",
            active=True,
            in_stock=True,
            price_minor=320000,
            tryon_supported=True,
            version=1,
        )
        catalog_uow.canonical_garments.add(garment)
        await catalog_uow.commit()

    save_uc = SaveToWardrobeUseCase(wardrobe_uow, profile_uow, catalog_uow)
    saved = await save_uc.execute(SaveToWardrobeCommand(user_id=user_a_id, garment_id=garment_id))
    item_id = saved.item_id

    # 1. User B attempts to delete User A's item -> 404 (not found / not owned)
    resp_intruder = client.delete(
        f"/wardrobe/items/{item_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert resp_intruder.status_code == 404

    # Item is still in wardrobe
    list_uc = ListWardrobeUseCase(wardrobe_uow)
    items = await list_uc.execute(user_a_id)
    assert len(items) == 1

    # 2. User A deletes their own item -> 204 No Content
    resp_owner = client.delete(
        f"/wardrobe/items/{item_id}",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert resp_owner.status_code == 204

    # Item is removed
    items_after = await list_uc.execute(user_a_id)
    assert len(items_after) == 0


@pytest.mark.asyncio
async def test_retailer_url_validation() -> None:
    """MVP 5.5: Retailer URL validator requires HTTPS, rejects credentials, and validates allowed hosts."""
    # 1. Non-HTTPS rejected
    with pytest.raises(ValidationError) as exc:
        validate_retailer_url("http://merchant.com/item/1")
    assert "HTTPS" in str(exc.value)

    # 2. Missing hostname rejected
    with pytest.raises(ValidationError) as exc:
        validate_retailer_url("https://")
    assert "hostname" in str(exc.value)

    # 3. Embedded credentials rejected
    with pytest.raises(ValidationError) as exc:
        validate_retailer_url("https://user:pass@merchant.com/item/1")
    assert "Credentials" in str(exc.value)

    # 4. Unapproved host rejected when allowed_hosts is enforced
    with pytest.raises(ValidationError) as exc:
        validate_retailer_url("https://malicious-site.com/p/1", allowed_hosts={"zara.com", "myntra.com"})
    assert "not approved" in str(exc.value)

    # 5. Valid approved host accepted
    valid_url = validate_retailer_url(
        "https://shop.myntra.com/jeans/123?color=blue",
        allowed_hosts={"myntra.com"},
    )
    assert valid_url == "https://shop.myntra.com/jeans/123?color=blue"


@pytest.mark.asyncio
async def test_buy_click_validates_garment_offer_relationship(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """MVP 5.5: CreateBuyClickUseCase validates that the requested offer belongs to the specified garment."""
    profile_uow = ProfileUnitOfWork(session_factory)
    catalog_uow = CatalogUnitOfWork(session_factory)
    commerce_uow = CommerceWardrobeUnitOfWork(session_factory)

    user_id = uuid4()
    garment_a_id = uuid4()
    garment_b_id = uuid4()

    async with profile_uow:
        profile_uow.users.add(User(id=user_id))
        await profile_uow.commit()

    async with catalog_uow:
        merchant = Merchant(name="Test Retailer", merchant_type="retailer")
        catalog_uow.merchants.add(merchant)
        await catalog_uow.flush()

        offer_b = MerchantOffer(
            garment_id=garment_b_id,
            merchant_id=merchant.id,
            source_product_id="SKU-B",
            url="https://merchant.com/b",
            price_minor=100000,
            currency="INR",
            in_stock=True,
        )
        catalog_uow.offers.add(offer_b)
        await catalog_uow.commit()
        offer_b_id = offer_b.id

    click_uc = CreateBuyClickUseCase(commerce_uow, profile_uow, catalog_uow)

    # Passing offer_b_id with garment_a_id -> Mismatch raises ValidationError
    with pytest.raises(ValidationError) as exc:
        await click_uc.execute(
            CreateBuyClickCommand(
                user_id=user_id,
                garment_id=garment_a_id,
                offer_id=offer_b_id,
            )
        )
    assert "does not belong" in str(exc.value)


@pytest.mark.asyncio
async def test_tryon_history_lists_user_jobs_with_signed_urls(
    session_factory: async_sessionmaker[AsyncSession],
    tmp_path,
) -> None:
    """MVP 5.6: GET /tryon/jobs lists authenticated user's try-on jobs with signed result URLs."""
    storage = LocalStorage(tmp_path)
    client, repo = create_test_client(session_factory, storage)

    identity = await repo.resolve("fashx-test", "user-history-test")
    user_id = UUID(identity.user_id)
    token = make_token(sub="user-history-test")

    profile_uow = ProfileUnitOfWork(session_factory)
    tryon_uow = TryOnUnitOfWork(session_factory)

    async with profile_uow:
        profile_uow.users.add(User(id=user_id))
        await profile_uow.commit()

    job_id = uuid4()
    art_key = f"art-{job_id}"
    res_key = f"u/{user_id}/tryon/{job_id}.jpg"
    storage.put(res_key, b"FAKE_RENDERED_IMAGE_BYTES")

    async with tryon_uow:
        job = TryOnJob(
            id=job_id,
            user_id=user_id,
            garment_id=uuid4(),
            profile_photo_id=uuid4(),
            idempotency_key=f"idemp-{job_id}",
            artifact_key=art_key,
            status="completed",
            model_version="tryon-v1.6",
            pipeline_version="pilot-pipe-v1",
        )
        tryon_uow.jobs.add(job)
        artifact = TryOnArtifact(
            job_id=job_id,
            artifact_key=art_key,
            result_key=res_key,
            model_version="tryon-v1.6",
            pipeline_version="pilot-pipe-v1",
            photo_version=1,
            garment_version=1,
        )
        tryon_uow.artifacts.add(artifact)
        await tryon_uow.commit()

    # 1. Unauthenticated request -> 401
    resp_unauth = client.get("/tryon/jobs", headers={"Authorization": ""})
    assert resp_unauth.status_code == 401

    # 2. Authenticated request -> 200 with signed result_url and expires_at
    resp = client.get("/tryon/jobs", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    jobs = resp.json()
    assert len(jobs) == 1
    assert jobs[0]["job_id"] == str(job_id)
    assert jobs[0]["status"] == "completed"
    assert jobs[0]["result_url"] is not None
    assert jobs[0]["expires_at"] is not None
