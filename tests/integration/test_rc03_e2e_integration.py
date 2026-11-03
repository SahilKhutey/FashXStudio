from __future__ import annotations

from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from database.models.catalog import CatalogSource, Merchant
from database.models.identity import User
from fashx.api.v1.me import get_profile_uow
from fashx.catalog.application.enrich_garment import EnrichGarmentCommand, EnrichGarmentUseCase
from fashx.catalog.application.ingest_product import (
    IngestMerchantProductUseCase,
    IngestProductCommand,
)
from fashx.catalog.router import get_catalog_uow
from fashx.main import app
from fashx.security.tokens import create_demo_token


@pytest.mark.asyncio
async def test_rc03_e2e_integration_flow() -> None:
    """Verify RC-03 end-to-end integration across health, identity, feed, commerce, and wardrobe."""
    token = create_demo_token(subject="rc03-tester-user")
    headers = {"Authorization": f"Bearer {token}"}
    client = TestClient(app, headers=headers)

    # 1. Health Probes
    live_res = client.get("/healthz/live")
    assert live_res.status_code == 200
    assert live_res.json()["status"] == "ok"

    ready_res = client.get("/healthz/ready")
    assert ready_res.status_code == 200
    assert ready_res.json()["database"] == "ok"

    # 2. Authenticated Identity
    me_res = client.get("/api/v1/me")
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert "user_id" in me_data
    user_id = UUID(me_data["user_id"])
    assert me_data["roles"] == ["user"]

    # 3. Setup user preferences and ingest test garment
    profile_uow = app.dependency_overrides[get_profile_uow]()
    catalog_uow = app.dependency_overrides[get_catalog_uow]()

    async with profile_uow:
        existing_user = await profile_uow.users.get_by_id(user_id)
        if not existing_user:
            profile_uow.users.add(User(id=user_id))
            await profile_uow.flush()

        await profile_uow.preferences.upsert_preferences(
            user_id,
            colors_favored=["navy", "white"],
            colors_avoided=[],
            categories=["tops"],
        )
        onboarding = await profile_uow.onboarding_profiles.create_if_missing(user_id)
        onboarding.styles = ["casual"]
        await profile_uow.consents.record_mobile_consent(user_id, "2026.1")
        await profile_uow.commit()

    async with catalog_uow:
        merchant = Merchant(name="RC03 Integrated Retailer", merchant_type="retailer")
        catalog_uow.merchants.add(merchant)
        await catalog_uow.flush()

        source = CatalogSource(
            slug=f"rc03-merchant-{merchant.id}",
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

    product = await ingest_uc.execute(
        IngestProductCommand(
            merchant_id=merchant_id,
            source_id=source_id,
            source_product_id="RC03-TOP-99",
            title="RC03 Tailored Linen Shirt",
            source_url="https://shop.example.com/products/rc03-top-99",
            category="tops",
            price_minor=199900,
            image_url="https://images.example.com/rc03-top.jpg",
        )
    )
    garment_id = product.canonical_garment_id
    await enrich_uc.execute(EnrichGarmentCommand(garment_id=garment_id))

    # 4. Discovery Feed Verification
    feed_res = client.get("/api/v1/feed?limit=10")
    assert feed_res.status_code == 200
    feed_data = feed_res.json()
    assert "items" in feed_data
    matching = [it for it in feed_data["items"] if it.get("garment_id") == str(garment_id)]
    assert len(matching) > 0
    item = matching[0]
    assert item["tryon_supported"] is True
    assert "stylist_explanation" in item

    # 5. Outbound Commerce Tracking & Safe Redirect
    buy_res = client.post(
        "/api/v1/commerce/buy-clicks",
        json={"garment_id": str(garment_id)},
    )
    assert buy_res.status_code == 201
    buy_data = buy_res.json()
    assert "tracking_id" in buy_data
    assert "redirect_url" in buy_data
    redirect_url = buy_data["redirect_url"]
    assert redirect_url.startswith("https://")
    assert "utm_source=fashx" in redirect_url
    assert "utm_campaign=vto_purchase" in redirect_url

    # 6. Wardrobe Persistence (Save, List, Remove)
    save_res = client.post(
        "/api/v1/wardrobe/items",
        json={"garment_id": str(garment_id)},
    )
    assert save_res.status_code == 201
    save_data = save_res.json()
    item_id = save_data["item_id"]
    assert item_id

    list_res = client.get("/api/v1/wardrobe/items")
    assert list_res.status_code == 200
    items = list_res.json()
    assert any(it["item_id"] == item_id for it in items)

    del_res = client.delete(f"/api/v1/wardrobe/items/{item_id}")
    assert del_res.status_code == 204

    # Confirm deletion
    list_res2 = client.get("/api/v1/wardrobe/items")
    assert list_res2.status_code == 200
    assert not any(it["item_id"] == item_id for it in list_res2.json())

    # 7. Virtual Try-On Jobs query
    jobs_res = client.get("/api/v1/tryon/jobs")
    assert jobs_res.status_code == 200
    assert isinstance(jobs_res.json(), list)
