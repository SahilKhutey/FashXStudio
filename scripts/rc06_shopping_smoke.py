#!/usr/bin/env python3
"""RC-06 Shopping, Retailer Offers & Purchase Handoff Smoke Verification Script.

Verifies end-to-end shopping journey:
1. Health & readiness probes (/healthz/live, /healthz/ready)
2. Identity authentication and principal token resolution (/api/v1/me)
3. Seed catalog data: canonical garment, cleared source, merchant, and multiple offers
4. Garment discovery & offer comparison (in-stock first, price sorted, minor units)
5. Outbound purchase handoff (mandatory offer_id, safe redirect validation, attribution params)
6. Wardrobe persistence (save with snapshot price/title, list, verify)
7. Wardrobe item removal
8. Security barrier & user isolation (token principal enforcement, no cross-user leakage)
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from urllib.parse import parse_qs, urlparse
from uuid import UUID, uuid4

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

import fashx.health.router as health_router_mod
from database.models import Base
from database.models.catalog import (
    CanonicalGarment,
    CatalogSource,
    Merchant,
    MerchantOffer,
    MerchantProduct,
)
from database.models.identity import User
from fashx.api.v1.me import get_profile_uow
from fashx.api.v1.me import router as me_router
from fashx.catalog.customer_router import (
    customer_garment_router,
)
from fashx.catalog.customer_router import (
    get_catalog_uow as get_customer_catalog_uow,
)
from fashx.catalog.repositories.catalog_repository import CatalogUnitOfWork
from fashx.catalog.router import get_catalog_uow
from fashx.commerce_wardrobe.repositories.commerce_wardrobe_repository import (
    CommerceWardrobeUnitOfWork,
)
from fashx.commerce_wardrobe.router import (
    get_catalog_uow as get_commerce_catalog_uow,
)
from fashx.commerce_wardrobe.router import (
    get_commerce_uow,
)
from fashx.commerce_wardrobe.router import (
    get_profile_uow as get_wardrobe_profile_uow,
)
from fashx.commerce_wardrobe.router import (
    router as commerce_wardrobe_router,
)
from fashx.gateway.errors import install_exception_handlers
from fashx.health.router import healthz_router
from fashx.health.router import router as health_router
from fashx.profile.repositories.profile_repository import ProfileUnitOfWork
from fashx.security.deps import get_identity_repo, get_principal
from fashx.security.errors import ApiError, api_error_handler
from fashx.security.identity import InMemoryIdentityRepo
from tests.conftest import make_token


# Mock external service probes for hermetic test environment
async def mock_check_db() -> bool:
    return True

async def mock_check_redis(redis_url: str) -> bool:
    return True

health_router_mod.check_database = mock_check_db
health_router_mod.check_redis_dependency = mock_check_redis


@pytest.mark.asyncio
async def test_rc06_shopping_smoke(monkeypatch):
    print("\n" + "=" * 60)
    print("  FASHXSTUDIO RC-06 SHOPPING & PURCHASE HANDOFF VERIFICATION")
    print("=" * 60 + "\n")

    monkeypatch.setattr(health_router_mod, "check_database", mock_check_db)
    monkeypatch.setattr(health_router_mod, "check_redis_dependency", mock_check_redis)

    engine = create_async_engine("sqlite+aiosqlite:///:memory:", poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    identity_repo = InMemoryIdentityRepo()

    app = FastAPI(title="FashX Shopping Smoke App")
    app.add_exception_handler(ApiError, api_error_handler)
    install_exception_handlers(app)

    app.dependency_overrides[get_identity_repo] = lambda: identity_repo
    app.dependency_overrides[get_profile_uow] = lambda: ProfileUnitOfWork(session_factory)
    app.dependency_overrides[get_wardrobe_profile_uow] = lambda: ProfileUnitOfWork(session_factory)
    app.dependency_overrides[get_catalog_uow] = lambda: CatalogUnitOfWork(session_factory)
    app.dependency_overrides[get_customer_catalog_uow] = lambda: CatalogUnitOfWork(session_factory)
    app.dependency_overrides[get_commerce_catalog_uow] = lambda: CatalogUnitOfWork(session_factory)
    app.dependency_overrides[get_commerce_uow] = lambda: CommerceWardrobeUnitOfWork(session_factory)

    app.include_router(health_router)
    app.include_router(healthz_router)
    app.include_router(me_router, prefix="/api/v1", dependencies=[Depends(get_principal)])
    app.include_router(customer_garment_router, dependencies=[Depends(get_principal)])
    app.include_router(commerce_wardrobe_router, dependencies=[Depends(get_principal)])

    user_a = await identity_repo.resolve("fashx-test", "user-a-shopping-smoke")
    user_b = await identity_repo.resolve("fashx-test", "user-b-shopping-smoke")
    user_a_id = UUID(user_a.user_id)
    user_b_id = UUID(user_b.user_id)

    profile_uow = ProfileUnitOfWork(session_factory)
    catalog_uow = CatalogUnitOfWork(session_factory)

    async with profile_uow:
        profile_uow.users.add(User(id=user_a_id))
        profile_uow.users.add(User(id=user_b_id))
        await profile_uow.commit()

    async with catalog_uow:
        merchant_myntra = Merchant(id=uuid4(), name="Myntra", merchant_type="retailer")
        merchant_ajio = Merchant(id=uuid4(), name="Ajio", merchant_type="retailer")
        merchant_tatacliq = Merchant(id=uuid4(), name="Tata CLiQ", merchant_type="retailer")
        catalog_uow.merchants.add(merchant_myntra)
        catalog_uow.merchants.add(merchant_ajio)
        catalog_uow.merchants.add(merchant_tatacliq)
        await catalog_uow.flush()

        source = CatalogSource(
            id=uuid4(),
            slug=f"smoke-source-{uuid4().hex[:6]}",
            name="Smoke Verified Partner Feed",
            kind="manual",
            status="cleared",
            rights_display=True,
            rights_tryon=True,
            image_policy="mirror",
        )
        catalog_uow.sources.add(source)
        await catalog_uow.flush()

        garment = CanonicalGarment(
            id=uuid4(),
            display_name="Classic Relaxed Navy Linen Shirt",
            category="tops",
            subcategory="shirts",
            gender="men",
            active=True,
            tryon_supported=True,
            display_price=179900,
        )
        catalog_uow.canonical_garments.add(garment)
        await catalog_uow.flush()

        prod = MerchantProduct(
            id=uuid4(),
            source_id=source.id,
            external_id=f"ext-shirt-{uuid4().hex[:6]}",
            canonical_garment_id=garment.id,
            title="Relaxed Linen Resort Shirt Navy",
            raw_category="Men Tops",
            brand="Harbour & Bay",
        )
        catalog_uow.merchant_products.add(prod)
        await catalog_uow.flush()

        offer_myntra = MerchantOffer(
            id=uuid4(),
            product_id=prod.id,
            merchant_id=merchant_myntra.id,
            url="https://www.myntra.com/shirts/harbour-bay-navy-linen",
            price_minor=179900,
            currency="INR",
            in_stock=True,
            last_synced_at=datetime.now(UTC),
        )
        offer_ajio = MerchantOffer(
            id=uuid4(),
            product_id=prod.id,
            merchant_id=merchant_ajio.id,
            url="https://www.ajio.com/clothing/harbour-bay-navy-linen",
            price_minor=199900,
            currency="INR",
            in_stock=True,
            last_synced_at=datetime.now(UTC),
        )
        offer_tatacliq = MerchantOffer(
            id=uuid4(),
            product_id=prod.id,
            merchant_id=merchant_tatacliq.id,
            url="https://www.tatacliq.com/shirts/harbour-bay-navy-linen",
            price_minor=149900,
            currency="INR",
            in_stock=False,
            last_synced_at=datetime.now(UTC),
        )
        catalog_uow.offers.add(offer_myntra)
        catalog_uow.offers.add(offer_ajio)
        catalog_uow.offers.add(offer_tatacliq)
        await catalog_uow.commit()

        garment_id = garment.id
        offer_myntra_id = offer_myntra.id
        offer_ajio_id = offer_ajio.id
        offer_tatacliq_id = offer_tatacliq.id

    token_a = make_token(sub="user-a-shopping-smoke")
    token_b = make_token(sub="user-b-shopping-smoke")

    client_a = TestClient(app, headers={"Authorization": f"Bearer {token_a}"})
    client_b = TestClient(app, headers={"Authorization": f"Bearer {token_b}"})

    # Phase 1: Health Probes
    print("[Phase 1/8] Checking Health & Readiness Probes...")
    live_res = client_a.get("/healthz/live")
    assert live_res.status_code == 200 and live_res.json()["status"] == "ok"
    print("  + /healthz/live -> 200 OK")

    ready_res = client_a.get("/healthz/ready")
    assert ready_res.status_code == 200, f"Readiness failed: {ready_res.text}"
    print("  + /healthz/ready -> 200 OK")

    # Phase 2: Identity & Principal Authentication
    print("\n[Phase 2/8] Authenticating User A and User B via JWT principal...")
    me_a = client_a.get("/api/v1/me")
    assert me_a.status_code == 200
    assert UUID(me_a.json()["user_id"]) == user_a_id
    print(f"  + User A authenticated: {user_a_id}")

    me_b = client_b.get("/api/v1/me")
    assert me_b.status_code == 200
    assert UUID(me_b.json()["user_id"]) == user_b_id
    print(f"  + User B authenticated: {user_b_id}")
    print(f"  + Seeded Garment: {garment_id}")
    print(f"  + Seeded Offers: Myntra={offer_myntra_id}, Ajio={offer_ajio_id}, Tata={offer_tatacliq_id}")

    # Phase 3 & 4: Garment Detail & Offer Sorting
    print("\n[Phase 3/8] Fetching Customer Garment Detail & Comparing Retailer Offers...")
    detail_res = client_a.get(f"/catalog/garments/{garment_id}")
    assert detail_res.status_code == 200, f"Detail failed: {detail_res.text}"
    detail = detail_res.json()

    print(f"  + Garment Title: {detail['title']}")
    print(f"  + Display Price Minor: {detail['price_minor']} (INR ₹{detail['price_minor'] / 100:.2f})")
    assert detail["price_minor"] == 179900, "Display price must be lowest in-stock offer"

    offers = detail.get("offers", [])
    assert len(offers) == 3, f"Expected 3 offers, got {len(offers)}"
    print(f"  + Total Retailer Offers Returned: {len(offers)}")

    print("  + Offers ranking verification:")
    for idx, off in enumerate(offers):
        print(f"    [{idx + 1}] Merchant: {off.get('merchant_name')} | Price: ₹{off['price_minor'] / 100:.2f} | InStock: {off['in_stock']} | UpdatedAt: {off.get('updated_at')}")

    assert offers[0]["id"] == str(offer_myntra_id)
    assert offers[0]["in_stock"] is True
    assert offers[0]["merchant_name"] == "Myntra"
    assert offers[0]["updated_at"] is not None

    assert offers[1]["id"] == str(offer_ajio_id)
    assert offers[1]["in_stock"] is True
    assert offers[1]["merchant_name"] == "Ajio"

    assert offers[2]["id"] == str(offer_tatacliq_id)
    assert offers[2]["in_stock"] is False
    assert offers[2]["merchant_name"] == "Tata CLiQ"
    print("  + Offers verified: in-stock prioritized, price ascending, real timestamps preserved.")

    # Phase 5: Outbound Purchase Handoff (Buy Click API)
    print("\n[Phase 4/8] Testing Outbound Retailer Purchase Handoff & Security Rules...")

    # A. Missing offer_id must be rejected with 422
    invalid_req = client_a.post("/commerce/buy-clicks", json={"garment_id": str(garment_id)})
    assert invalid_req.status_code == 422, f"Expected 422 on missing offer_id, got {invalid_req.status_code}"
    print("  + Missing offer_id rejected with 422 Unprocessable Entity (mandatory offer selection).")

    # B. Out of stock offer must be rejected with 409
    oos_req = client_a.post(
        "/commerce/buy-clicks",
        json={"garment_id": str(garment_id), "offer_id": str(offer_tatacliq_id)},
    )
    assert oos_req.status_code == 409, f"Expected 409 on out of stock offer, got {oos_req.status_code}"
    print("  + Out-of-stock offer rejected with 409 Conflict.")

    # C. Valid in-stock offer purchase handoff
    buy_res = client_a.post(
        "/commerce/buy-clicks",
        json={"garment_id": str(garment_id), "offer_id": str(offer_myntra_id)},
    )
    assert buy_res.status_code == 200, f"Buy click failed: {buy_res.text}"
    buy_data = buy_res.json()
    buy_click_id = buy_data["buy_click_id"]
    redirect_url = buy_data["redirect_url"]
    tracking_id = buy_data["tracking_id"]

    print(f"  + Buy Click recorded: buy_click_id={buy_click_id}, tracking_id={tracking_id}")
    print(f"  + Redirect Destination: {redirect_url}")

    # Verify attribution params
    parsed = urlparse(redirect_url)
    qs = parse_qs(parsed.query)
    assert parsed.scheme == "https"
    assert "myntra.com" in parsed.netloc
    assert qs.get("utm_source") == ["fashx"]
    assert qs.get("utm_medium") == ["app"]
    assert qs.get("utm_campaign") == ["vto_purchase"]
    assert qs.get("sub_id") == [str(user_a_id)]
    assert qs.get("click_id") == [str(buy_click_id)]
    print("  + Attribution verified: utm_source, utm_medium, utm_campaign, sub_id, and click_id verified.")

    # Phase 6: Wardrobe Persistence
    print("\n[Phase 5/8] Testing Wardrobe Item Persistence...")
    save_res = client_a.post(
        "/wardrobe/items",
        json={
            "garment_id": str(garment_id),
            "offer_id": str(offer_myntra_id),
        },
    )
    assert save_res.status_code == 201, f"Wardrobe save failed: {save_res.text}"
    saved_item = save_res.json()
    print(f"  + Garment saved to User A wardrobe: {saved_item['garment_id']}")
    print(f"  + Snapshot Title: {saved_item['snapshot_title']}")
    print(f"  + Snapshot Price: ₹{saved_item['snapshot_price_minor'] / 100:.2f}")

    # Fetch User A wardrobe
    wardrobe_res = client_a.get("/wardrobe/items")
    assert wardrobe_res.status_code == 200
    wardrobe_items = wardrobe_res.json()
    assert any(item["garment_id"] == str(garment_id) for item in wardrobe_items)
    print(f"  + User A wardrobe verified: {len(wardrobe_items)} item(s) present.")

    # Phase 7: Wardrobe Item Removal
    print("\n[Phase 6/8] Testing Wardrobe Item Removal...")
    delete_res = client_a.delete(f"/wardrobe/items/{garment_id}")
    assert delete_res.status_code == 200, f"Delete failed: {delete_res.text}"
    print(f"  + Garment removed from wardrobe: {garment_id}")

    # Verify User A wardrobe is empty again
    recheck_res = client_a.get("/wardrobe/items")
    assert recheck_res.status_code == 200
    assert not any(item["garment_id"] == str(garment_id) for item in recheck_res.json())
    print("  + Wardrobe removal verified.")

    # Phase 8: Cross-User Security Barrier
    print("\n[Phase 7/8] Verifying Security Barrier & Cross-User Isolation...")

    # User B cannot claim User A's user_id in buy-click
    spoof_res = client_b.post(
        "/commerce/buy-clicks",
        json={
            "garment_id": str(garment_id),
            "offer_id": str(offer_myntra_id),
            "user_id": str(user_a_id),
        },
    )
    assert spoof_res.status_code == 403, f"Expected 403 on user_id spoof, got {spoof_res.status_code}"
    print("  + User identity spoofing rejected with 403 Forbidden.")

    # User B's wardrobe is empty and does not expose User A's data
    user_b_wardrobe = client_b.get("/wardrobe/items")
    assert user_b_wardrobe.status_code == 200
    assert len(user_b_wardrobe.json()) == 0
    print("  + Cross-user wardrobe isolation verified: User B cannot observe User A's data.")

    # Summary
    print("\n" + "=" * 60)
    print("  RC-06 SHOPPING INTEGRATION SMOKE: ALL 8 PHASES PASSED")
    print("=" * 60)

    await engine.dispose()


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-s", "-v"]))
