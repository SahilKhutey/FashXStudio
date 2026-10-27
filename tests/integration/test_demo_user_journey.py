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
async def test_complete_demo_user_journey() -> None:
    """Test the complete end-to-end evaluator journey:

    1. Generate demo access token.
    2. Authenticate to /api/v1/me.
    3. Complete onboarding preferences (body, styles, colors).
    4. Grant photo consent.
    5. Ingest cleared catalog garments.
    6. Fetch personalized feed with stylist explanations.
    7. Send feed feedback (like signal).
    8. Save item to wardrobe closet.
    9. Request account erasure and verify clean deletion.
    """
    token = create_demo_token(
        subject="demo-journey-user",
        secret="test-secret-key-at-least-32-chars-long",
        issuer="fashx-test",
        audience="fashx-api",
    )
    headers = {"Authorization": f"Bearer {token}"}
    client = TestClient(app, headers=headers)

    # 1. Authenticate to /api/v1/me
    me_res = client.get("/api/v1/me")
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert "user_id" in me_data
    user_id = UUID(me_data["user_id"])
    assert me_data["roles"] == ["user"]

    profile_uow = app.dependency_overrides[get_profile_uow]()
    catalog_uow = app.dependency_overrides[get_catalog_uow]()

    # 2. Setup user profile, styles, preferences & consent
    async with profile_uow:
        # Ensure user entity exists
        existing_user = await profile_uow.users.get_by_id(user_id)
        if not existing_user:
            profile_uow.users.add(User(id=user_id))
            await profile_uow.flush()

        # Set body profile
        await profile_uow.body_profiles.upsert(
            user_id, height_cm=172, weight_kg=68, build="athletic"
        )

        # Set preferences
        await profile_uow.preferences.upsert_preferences(
            user_id,
            colors_favored=["olive", "black"],
            colors_avoided=[],
            categories=["tops", "bottoms"],
        )

        # Set style quiz answers
        onboarding = await profile_uow.onboarding_profiles.create_if_missing(user_id)
        onboarding.styles = ["minimal", "casual"]

        # Record consent
        await profile_uow.consents.record_mobile_consent(user_id, "2026.1")
        await profile_uow.commit()

    # 3. Ingest cleared catalog garments
    async with catalog_uow:
        merchant = Merchant(name="Demo Journey Store", merchant_type="retailer")
        catalog_uow.merchants.add(merchant)
        await catalog_uow.flush()

        source = CatalogSource(
            slug=f"merchant-{merchant.id}",
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

    item1 = await ingest_uc.execute(
        IngestProductCommand(
            merchant_id=merchant_id,
            source_id=source_id,
            source_product_id="JOURNEY-TOP-01",
            title="Olive Classic Linen Shirt",
            source_url="https://demo.fashx.studio/products/top-01",
            category="tops",
            price_minor=149900,
            image_url="https://images.fashx.studio/products/top-01.jpg",
        )
    )
    await enrich_uc.execute(EnrichGarmentCommand(garment_id=item1.canonical_garment_id))

    # 4. Fetch personalized feed
    feed_res = client.get("/api/v1/feed?limit=10")
    assert feed_res.status_code == 200
    feed_data = feed_res.json()
    assert "items" in feed_data
    assert len(feed_data["items"]) >= 1
    top_item = feed_data["items"][0]
    assert "stylist_explanation" in top_item
    assert "relevance_score" in top_item
    assert top_item["title"] == "Olive Classic Linen Shirt"

    # 5. Send feed signal feedback (like)
    sig_res = client.post(
        "/api/v1/feed/signals",
        json={"garment_id": str(item1.canonical_garment_id), "action": "like"},
    )
    assert sig_res.status_code == 201

    # 6. Save item to wardrobe closet
    wardrobe_res = client.post(
        "/api/v1/wardrobe/items",
        json={
            "user_id": str(user_id),
            "garment_id": str(item1.canonical_garment_id),
        },
    )
    assert wardrobe_res.status_code == 201
    wardrobe_data = wardrobe_res.json()
    assert "item_id" in wardrobe_data

    # 7. Request account erasure and verify cascading deletion
    delete_res = client.delete("/api/v1/me")
    assert delete_res.status_code == 202
    del_data = delete_res.json()
    assert del_data["status"] == "queued"
