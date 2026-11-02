from __future__ import annotations

from typing import Any
from urllib.parse import parse_qs, urlparse
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from database.models.catalog import (
    CanonicalGarment,
    CatalogSource,
    Merchant,
    MerchantOffer,
    MerchantProduct,
)
from database.models.identity import User
from database.models.tryon import TryOnArtifact, TryOnJob
from fashx.catalog.repositories.catalog_repository import CatalogUnitOfWork
from fashx.commerce_wardrobe.application.create_buy_click import (
    CreateBuyClickCommand,
    CreateBuyClickUseCase,
    validate_retailer_url,
)
from fashx.commerce_wardrobe.repositories.commerce_wardrobe_repository import (
    CommerceWardrobeUnitOfWork,
)
from fashx.commerce_wardrobe.router import (
    get_catalog_uow,
    get_commerce_uow,
    get_profile_uow,
    get_tryon_uow,
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
from fashx.tryon.router import (
    get_profile_uow as get_tryon_profile_uow,
)
from fashx.tryon.router import (
    get_tryon_uow as get_tryon_router_uow,
)
from fashx.tryon.router import (
    router as tryon_router,
)
from tests.conftest import make_token

# -----------------------------------------------------------------------------
# 1. Retailer URL Validation Unit Tests
# -----------------------------------------------------------------------------


def test_retailer_url_requires_https():
    with pytest.raises(ValidationError, match="HTTPS"):
        validate_retailer_url("http://shop.example.com/item/1")


def test_retailer_url_rejects_credentials():
    with pytest.raises(ValidationError, match="Credentials"):
        validate_retailer_url("https://user:password@shop.example.com/item/1")


def test_retailer_url_rejects_unapproved_domain():
    with pytest.raises(ValidationError, match="not approved"):
        validate_retailer_url(
            "https://fake-retailer.example/item/1",
            allowed_hosts={"myntra.com"},
        )


def test_retailer_url_accepts_approved_subdomain():
    result = validate_retailer_url(
        "https://www.myntra.com/item/1",
        allowed_hosts={"myntra.com"},
    )
    assert result == "https://www.myntra.com/item/1"


# -----------------------------------------------------------------------------
# 2. Integration Test Setup
# -----------------------------------------------------------------------------


def _create_test_app(
    session_factory: async_sessionmaker[AsyncSession],
    storage: Any,
) -> tuple[TestClient, InMemoryIdentityRepo]:
    app = FastAPI()
    app.add_exception_handler(ApiError, api_error_handler)
    install_exception_handlers(app)
    repo = InMemoryIdentityRepo()

    app.dependency_overrides[get_identity_repo] = lambda: repo
    app.dependency_overrides[get_commerce_uow] = lambda: CommerceWardrobeUnitOfWork(session_factory)
    app.dependency_overrides[get_profile_uow] = lambda: ProfileUnitOfWork(session_factory)
    app.dependency_overrides[get_tryon_profile_uow] = lambda: ProfileUnitOfWork(session_factory)
    app.dependency_overrides[get_catalog_uow] = lambda: CatalogUnitOfWork(session_factory)
    app.dependency_overrides[get_tryon_uow] = lambda: TryOnUnitOfWork(session_factory)
    app.dependency_overrides[get_tryon_router_uow] = lambda: TryOnUnitOfWork(session_factory)
    app.dependency_overrides[get_session_factory] = lambda: session_factory
    app.dependency_overrides[get_storage] = lambda: storage

    app.include_router(commerce_router)
    app.include_router(tryon_router)
    return TestClient(app), repo


async def _seed_test_entities(
    session_factory: async_sessionmaker[AsyncSession],
    user_id: UUID,
    garment_id: UUID,
    other_garment_id: UUID,
) -> tuple[UUID, UUID, UUID, UUID]:
    """Seeds merchant, catalog source, canonical garments, products, offers, jobs, and artifacts."""
    profile_uow = ProfileUnitOfWork(session_factory)
    catalog_uow = CatalogUnitOfWork(session_factory)
    tryon_uow = TryOnUnitOfWork(session_factory)

    async with profile_uow:
        profile_uow.users.add(User(id=user_id))
        await profile_uow.commit()

    merchant_id = uuid4()
    source_id = uuid4()
    in_stock_offer_id = uuid4()
    out_of_stock_offer_id = uuid4()

    async with catalog_uow:
        merchant = Merchant(id=merchant_id, name="Test Retailer", merchant_type="retailer")
        catalog_uow.merchants.add(merchant)
        source = CatalogSource(
            id=source_id,
            slug=f"retailer-{merchant_id}",
            name="Test Source",
            kind="manual",
            status="cleared",
            rights_display=True,
            rights_tryon=True,
            image_policy="mirror",
        )
        catalog_uow.sources.add(source)

        g1 = CanonicalGarment(
            id=garment_id,
            display_name="Classic Linen Shirt",
            category="tops",
            subcategory="shirts",
            active=True,
        )
        g2 = CanonicalGarment(
            id=other_garment_id,
            display_name="Denim Jeans",
            category="bottoms",
            active=True,
        )
        catalog_uow.canonical_garments.add(g1)
        catalog_uow.canonical_garments.add(g2)

        p1 = MerchantProduct(
            id=uuid4(),
            merchant_id=merchant_id,
            source_id=source_id,
            canonical_garment_id=garment_id,
            source_product_id="PROD-LINEN-1",
            title="Classic Linen Shirt",
            source_url="https://www.myntra.com/shirt/linen-1",
        )
        p2 = MerchantProduct(
            id=uuid4(),
            merchant_id=merchant_id,
            source_id=source_id,
            canonical_garment_id=garment_id,
            source_product_id="PROD-OOS-1",
            title="Out Of Stock Shirt",
            source_url="https://www.myntra.com/shirt/oos-1",
        )
        catalog_uow.merchant_products.add(p1)
        catalog_uow.merchant_products.add(p2)

        offer1 = MerchantOffer(
            id=in_stock_offer_id,
            garment_id=garment_id,
            merchant_id=merchant_id,
            source_product_id="PROD-LINEN-1",
            url="https://www.myntra.com/shirt/linen-1",
            price_minor=199900,
            currency="INR",
            in_stock=True,
        )
        offer2 = MerchantOffer(
            id=out_of_stock_offer_id,
            garment_id=garment_id,
            merchant_id=merchant_id,
            source_product_id="PROD-OOS-1",
            url="https://www.myntra.com/shirt/oos-1",
            price_minor=149900,
            currency="INR",
            in_stock=False,
        )
        catalog_uow.offers.add(offer1)
        catalog_uow.offers.add(offer2)
        await catalog_uow.commit()

    # Create completed try-on job and artifact for user
    job_id = uuid4()
    artifact_id = uuid4()
    async with tryon_uow:
        job = TryOnJob(
            id=job_id,
            user_id=user_id,
            garment_id=garment_id,
            profile_photo_id=uuid4(),
            idempotency_key=f"idemp-{job_id}",
            status="completed",
            artifact_key=f"u/{user_id}/tryon/{job_id}.png",
            model_version="tryon-v1.6",
            pipeline_version="1.0.0",
        )
        tryon_uow.jobs.add(job)
        artifact = TryOnArtifact(
            id=artifact_id,
            job_id=job_id,
            artifact_key=f"u/{user_id}/tryon/{job_id}.png",
            result_key=f"u/{user_id}/tryon/{job_id}.png",
            model_version="tryon-v1.6",
            pipeline_version="1.0.0",
            photo_version=1,
            garment_version=1,
            width=768,
            height=1024,
            size_bytes=100000,
            content_type="image/png",
            content_sha256="abc123sha",
        )
        tryon_uow.artifacts.add(artifact)
        await tryon_uow.commit()

    return in_stock_offer_id, out_of_stock_offer_id, job_id, artifact_id


# -----------------------------------------------------------------------------
# 3. Wardrobe Artifact Ownership & Garment Validation Tests
# -----------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_save_tryon_with_matching_owner_and_garment_succeeds(
    session_factory: async_sessionmaker[AsyncSession],
    tmp_path,
) -> None:
    storage = LocalStorage(tmp_path)
    client, repo = _create_test_app(session_factory, storage)

    user_id = UUID((await repo.resolve("fashx-test", "user-phase8-owner")).user_id)
    token = make_token(sub="user-phase8-owner")
    garment_id = uuid4()
    other_garment_id = uuid4()

    _, _, _, artifact_id = await _seed_test_entities(
        session_factory, user_id, garment_id, other_garment_id
    )

    resp = client.post(
        "/wardrobe/items",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "garment_id": str(garment_id),
            "tryon_artifact_id": str(artifact_id),
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["garment_id"] == str(garment_id)
    assert data["tryon_artifact_id"] == str(artifact_id)
    assert "Classic Linen Shirt" in data["snapshot_title"]


@pytest.mark.asyncio
async def test_save_tryon_artifact_belonging_to_another_user_is_rejected(
    session_factory: async_sessionmaker[AsyncSession],
    tmp_path,
) -> None:
    storage = LocalStorage(tmp_path)
    client, repo = _create_test_app(session_factory, storage)

    owner_id = UUID((await repo.resolve("fashx-test", "user-phase8-owner")).user_id)
    attacker_id = UUID((await repo.resolve("fashx-test", "user-phase8-attacker")).user_id)
    attacker_token = make_token(sub="user-phase8-attacker")
    garment_id = uuid4()
    other_garment_id = uuid4()

    _, _, _, owner_artifact_id = await _seed_test_entities(
        session_factory, owner_id, garment_id, other_garment_id
    )

    # Register attacker in profile repo
    profile_uow = ProfileUnitOfWork(session_factory)
    async with profile_uow:
        profile_uow.users.add(User(id=attacker_id))
        await profile_uow.commit()

    resp = client.post(
        "/wardrobe/items",
        headers={"Authorization": f"Bearer {attacker_token}"},
        json={
            "garment_id": str(garment_id),
            "tryon_artifact_id": str(owner_artifact_id),
        },
    )
    assert resp.status_code == 403
    assert "Try-on artifact does not belong to this user" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_save_tryon_artifact_belonging_to_another_garment_is_rejected(
    session_factory: async_sessionmaker[AsyncSession],
    tmp_path,
) -> None:
    storage = LocalStorage(tmp_path)
    client, repo = _create_test_app(session_factory, storage)

    user_id = UUID((await repo.resolve("fashx-test", "user-phase8-mismatch")).user_id)
    token = make_token(sub="user-phase8-mismatch")
    garment_id = uuid4()
    other_garment_id = uuid4()

    _, _, _, artifact_id = await _seed_test_entities(
        session_factory, user_id, garment_id, other_garment_id
    )

    # Attempt to attach artifact for garment_id to other_garment_id
    resp = client.post(
        "/wardrobe/items",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "garment_id": str(other_garment_id),
            "tryon_artifact_id": str(artifact_id),
        },
    )
    assert resp.status_code == 403
    assert "Try-on artifact does not belong to this user and garment" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_save_non_existent_artifact_uuid_is_rejected(
    session_factory: async_sessionmaker[AsyncSession],
    tmp_path,
) -> None:
    storage = LocalStorage(tmp_path)
    client, repo = _create_test_app(session_factory, storage)

    user_id = UUID((await repo.resolve("fashx-test", "user-phase8-nonexistent")).user_id)
    token = make_token(sub="user-phase8-nonexistent")
    garment_id = uuid4()
    other_garment_id = uuid4()

    await _seed_test_entities(session_factory, user_id, garment_id, other_garment_id)

    missing_artifact_id = uuid4()
    resp = client.post(
        "/wardrobe/items",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "garment_id": str(garment_id),
            "tryon_artifact_id": str(missing_artifact_id),
        },
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_save_same_garment_twice_is_idempotent(
    session_factory: async_sessionmaker[AsyncSession],
    tmp_path,
) -> None:
    storage = LocalStorage(tmp_path)
    client, repo = _create_test_app(session_factory, storage)

    user_id = UUID((await repo.resolve("fashx-test", "user-phase8-idemp")).user_id)
    token = make_token(sub="user-phase8-idemp")
    garment_id = uuid4()
    other_garment_id = uuid4()

    _, _, _, artifact_id = await _seed_test_entities(
        session_factory, user_id, garment_id, other_garment_id
    )

    resp1 = client.post(
        "/wardrobe/items",
        headers={"Authorization": f"Bearer {token}"},
        json={"garment_id": str(garment_id), "tryon_artifact_id": str(artifact_id)},
    )
    assert resp1.status_code == 201

    resp2 = client.post(
        "/wardrobe/items",
        headers={"Authorization": f"Bearer {token}"},
        json={"garment_id": str(garment_id), "tryon_artifact_id": str(artifact_id)},
    )
    assert resp2.status_code == 201

    assert resp1.json()["item_id"] == resp2.json()["item_id"]

    # Verify only one item in wardrobe
    list_resp = client.get(
        "/wardrobe/items",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1


@pytest.mark.asyncio
async def test_wardrobe_list_is_isolated_to_authenticated_user(
    session_factory: async_sessionmaker[AsyncSession],
    tmp_path,
) -> None:
    storage = LocalStorage(tmp_path)
    client, repo = _create_test_app(session_factory, storage)

    user1_id = UUID((await repo.resolve("fashx-test", "user1-closet")).user_id)
    token1 = make_token(sub="user1-closet")
    user2_id = UUID((await repo.resolve("fashx-test", "user2-closet")).user_id)
    token2 = make_token(sub="user2-closet")

    garment_id = uuid4()
    other_garment_id = uuid4()
    await _seed_test_entities(session_factory, user1_id, garment_id, other_garment_id)

    profile_uow = ProfileUnitOfWork(session_factory)
    async with profile_uow:
        profile_uow.users.add(User(id=user2_id))
        await profile_uow.commit()

    # User 1 saves item
    client.post(
        "/wardrobe/items",
        headers={"Authorization": f"Bearer {token1}"},
        json={"garment_id": str(garment_id)},
    )

    # User 2 lists wardrobe -> empty
    resp = client.get(
        "/wardrobe/items",
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert resp.status_code == 200
    assert len(resp.json()) == 0


@pytest.mark.asyncio
async def test_remove_another_users_wardrobe_item_fails(
    session_factory: async_sessionmaker[AsyncSession],
    tmp_path,
) -> None:
    storage = LocalStorage(tmp_path)
    client, repo = _create_test_app(session_factory, storage)

    user1_id = UUID((await repo.resolve("fashx-test", "user1-remove")).user_id)
    token1 = make_token(sub="user1-remove")
    user2_id = UUID((await repo.resolve("fashx-test", "user2-remove")).user_id)
    token2 = make_token(sub="user2-remove")

    garment_id = uuid4()
    other_garment_id = uuid4()
    await _seed_test_entities(session_factory, user1_id, garment_id, other_garment_id)

    profile_uow = ProfileUnitOfWork(session_factory)
    async with profile_uow:
        profile_uow.users.add(User(id=user2_id))
        await profile_uow.commit()

    save_resp = client.post(
        "/wardrobe/items",
        headers={"Authorization": f"Bearer {token1}"},
        json={"garment_id": str(garment_id)},
    )
    item_id = save_resp.json()["item_id"]

    # User 2 attempts to delete User 1's item
    del_resp = client.delete(
        f"/wardrobe/items/{item_id}",
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert del_resp.status_code == 404


# -----------------------------------------------------------------------------
# 4. Commerce Buy-Click & Retailer Handoff Tests
# -----------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_buy_click_rejects_offer_belonging_to_another_garment(
    session_factory: async_sessionmaker[AsyncSession],
    tmp_path,
) -> None:
    storage = LocalStorage(tmp_path)
    client, repo = _create_test_app(session_factory, storage)

    user_id = UUID((await repo.resolve("fashx-test", "user-buy-mismatch")).user_id)
    token = make_token(sub="user-buy-mismatch")
    garment_id = uuid4()
    other_garment_id = uuid4()

    offer_id, _, _, _ = await _seed_test_entities(
        session_factory, user_id, garment_id, other_garment_id
    )

    # Pass other_garment_id with offer_id (which belongs to garment_id)
    resp = client.post(
        "/commerce/buy-clicks",
        headers={"Authorization": f"Bearer {token}"},
        json={"garment_id": str(other_garment_id), "offer_id": str(offer_id)},
    )
    assert resp.status_code == 422
    assert "does not belong to garment" in resp.json()["error"]["message"]


@pytest.mark.asyncio
async def test_buy_click_rejects_out_of_stock_offer(
    session_factory: async_sessionmaker[AsyncSession],
    tmp_path,
) -> None:
    storage = LocalStorage(tmp_path)
    client, repo = _create_test_app(session_factory, storage)

    user_id = UUID((await repo.resolve("fashx-test", "user-buy-oos")).user_id)
    token = make_token(sub="user-buy-oos")
    garment_id = uuid4()
    other_garment_id = uuid4()

    _, oos_offer_id, _, _ = await _seed_test_entities(
        session_factory, user_id, garment_id, other_garment_id
    )

    resp = client.post(
        "/commerce/buy-clicks",
        headers={"Authorization": f"Bearer {token}"},
        json={"garment_id": str(garment_id), "offer_id": str(oos_offer_id)},
    )
    assert resp.status_code == 422
    assert "currently out of stock" in resp.json()["error"]["message"]


@pytest.mark.asyncio
async def test_buy_click_rejects_unapproved_retailer_host(
    session_factory: async_sessionmaker[AsyncSession],
    tmp_path,
) -> None:
    profile_uow = ProfileUnitOfWork(session_factory)
    catalog_uow = CatalogUnitOfWork(session_factory)
    commerce_uow = CommerceWardrobeUnitOfWork(session_factory)

    user_id = uuid4()
    garment_id = uuid4()
    merchant_id = uuid4()
    source_id = uuid4()
    offer_id = uuid4()

    async with profile_uow:
        profile_uow.users.add(User(id=user_id))
        await profile_uow.commit()

    async with catalog_uow:
        merchant = Merchant(id=merchant_id, name="Untrusted Merchant", merchant_type="retailer")
        source = CatalogSource(
            id=source_id,
            slug=f"untrusted-{merchant_id}",
            name="Untrusted",
            kind="manual",
            status="cleared",
            rights_display=True,
            rights_tryon=True,
            image_policy="mirror",
        )
        catalog_uow.merchants.add(merchant)
        catalog_uow.sources.add(source)
        catalog_uow.canonical_garments.add(
            CanonicalGarment(id=garment_id, display_name="Item", category="tops", active=True)
        )
        catalog_uow.merchant_products.add(
            MerchantProduct(
                id=uuid4(),
                merchant_id=merchant_id,
                source_id=source_id,
                canonical_garment_id=garment_id,
                source_product_id="ITEM-EVIL",
                title="Bad URL Product",
                source_url="https://phishing-site.example/buy",
            )
        )
        catalog_uow.offers.add(
            MerchantOffer(
                id=offer_id,
                garment_id=garment_id,
                merchant_id=merchant_id,
                source_product_id="ITEM-EVIL",
                url="https://phishing-site.example/buy",
                price_minor=10000,
                in_stock=True,
            )
        )
        await catalog_uow.commit()

    use_case = CreateBuyClickUseCase(
        commerce_uow=commerce_uow,
        profile_uow=profile_uow,
        catalog_uow=catalog_uow,
        allowed_hosts={"myntra.com", "amazon.in"},
    )

    with pytest.raises(ValidationError, match="not approved"):
        await use_case.execute(
            CreateBuyClickCommand(
                user_id=user_id,
                garment_id=garment_id,
                offer_id=offer_id,
            )
        )


@pytest.mark.asyncio
async def test_buy_click_valid_offer_records_click_and_returns_attributed_redirect(
    session_factory: async_sessionmaker[AsyncSession],
    tmp_path,
) -> None:
    storage = LocalStorage(tmp_path)
    client, repo = _create_test_app(session_factory, storage)

    user_id = UUID((await repo.resolve("fashx-test", "user-buy-valid")).user_id)
    token = make_token(sub="user-buy-valid")
    garment_id = uuid4()
    other_garment_id = uuid4()

    offer_id, _, _, _ = await _seed_test_entities(
        session_factory, user_id, garment_id, other_garment_id
    )

    resp = client.post(
        "/commerce/buy-clicks",
        headers={"Authorization": f"Bearer {token}"},
        json={"garment_id": str(garment_id), "offer_id": str(offer_id)},
    )
    assert resp.status_code == 201
    data = resp.json()

    assert "buy_click_id" in data
    assert "tracking_id" in data
    assert "fashx_" in data["tracking_id"]

    redirect_url = data["redirect_url"]
    parsed = urlparse(redirect_url)
    assert parsed.scheme == "https"
    assert parsed.netloc == "www.myntra.com"

    params = parse_qs(parsed.query)
    assert params["utm_source"] == ["fashx"]
    assert params["utm_medium"] == ["app"]
    assert params["utm_campaign"] == ["vto_purchase"]
    assert params["sub_id"] == [data["tracking_id"]]
    assert params["click_id"] == [data["buy_click_id"]]


# -----------------------------------------------------------------------------
# 5. Try-On Job Status Contract Extension Test
# -----------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_tryon_status_returns_canonical_garment_and_artifact_id(
    session_factory: async_sessionmaker[AsyncSession],
    tmp_path,
) -> None:
    storage = LocalStorage(tmp_path)
    client, repo = _create_test_app(session_factory, storage)

    user_id = UUID((await repo.resolve("fashx-test", "user-status-test")).user_id)
    token = make_token(sub="user-status-test")
    garment_id = uuid4()
    other_garment_id = uuid4()

    _, _, job_id, artifact_id = await _seed_test_entities(
        session_factory, user_id, garment_id, other_garment_id
    )

    resp = client.get(
        f"/tryon/jobs/{job_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()

    assert data["job_id"] == str(job_id)
    assert data["garment_id"] == str(garment_id)
    assert data["artifact_id"] == str(artifact_id)
    assert data["status"] == "completed"
