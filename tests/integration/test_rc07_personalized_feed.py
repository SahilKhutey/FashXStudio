from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from database.models.catalog import (
    Brand,
    CanonicalGarment,
    CatalogSource,
    GarmentEnrichment,
    Merchant,
    MerchantOffer,
    MerchantProduct,
)
from database.models.identity import User
from database.models.profile import OnboardingProfile, UserPreference
from fashx.catalog.router import get_catalog_uow
from fashx.main import app
from fashx.recommendation.router import get_profile_uow
from fashx.security.deps import get_identity_repo
from tests.conftest import make_token


@pytest.fixture
def api_client():
    return TestClient(app)


@pytest.mark.asyncio
async def test_personalized_feed_lifecycle_and_exclusion(api_client: TestClient) -> None:
    repo = app.dependency_overrides[get_identity_repo]()
    identity = await repo.resolve("fashx-test", "user-rc07-pers")
    user_id = uuid.UUID(identity.user_id)
    token = make_token(sub="user-rc07-pers")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Setup user with preferences
    profile_uow = app.dependency_overrides[get_profile_uow]()
    async with profile_uow:
        profile_uow.users.add(User(id=user_id))
        profile_uow.session.add(
            OnboardingProfile(
                user_id=user_id,
                styles=["casual", "minimalist"],
                status="completed",
                step="done",
            )
        )
        profile_uow.session.add(
            UserPreference(
                user_id=user_id,
                budget_min=1000,
                budget_max=6000,
                categories=["tops", "dresses"],
                colors_favored=["navy", "white"],
                colors_avoided=["yellow"],
            )
        )
        await profile_uow.commit()

    # 2. Setup catalog items
    catalog_uow = app.dependency_overrides[get_catalog_uow]()
    brand_id = uuid.uuid4()
    source_id = uuid.uuid4()
    merchant_id = uuid.uuid4()

    g1_id = uuid.uuid4()  # In-budget navy casual top
    g2_id = uuid.uuid4()  # In-budget white minimalist top
    g3_id = uuid.uuid4()  # Yellow top (avoided color) -> should be filtered

    async with catalog_uow:
        catalog_uow.session.add(Brand(id=brand_id, name="Studio Brand", normalized_name="studio-brand"))
        catalog_uow.session.add(
            CatalogSource(
                id=source_id,
                slug=f"source-{uuid.uuid4().hex[:6]}",
                name="Test Source",
                kind="test",
                status="cleared",
                rights_display=True,
                rights_tryon=True,
            )
        )
        catalog_uow.session.add(Merchant(id=merchant_id, name="Test Merchant", merchant_type="retailer"))

        g1 = CanonicalGarment(
            id=g1_id,
            brand_id=brand_id,
            display_name="Navy Linen Shirt",
            category="tops",
            subcategory="shirt",
            gender="women",
            active=True,
            in_stock=True,
            price_minor=3500,
            tryon_supported=True,
        )
        g2 = CanonicalGarment(
            id=g2_id,
            brand_id=brand_id,
            display_name="White Minimalist Blouse",
            category="tops",
            subcategory="blouse",
            gender="women",
            active=True,
            in_stock=True,
            price_minor=4200,
            tryon_supported=True,
        )
        g3 = CanonicalGarment(
            id=g3_id,
            brand_id=brand_id,
            display_name="Yellow Summer Top",
            category="tops",
            subcategory="top",
            gender="women",
            active=True,
            in_stock=True,
            price_minor=2500,
            tryon_supported=True,
        )
        catalog_uow.session.add_all([g1, g2, g3])

        # Add products and offers
        for gid, price in ((g1_id, 3500), (g2_id, 4200), (g3_id, 2500)):
            sp_id = f"sp-{gid.hex[:6]}"
            mp = MerchantProduct(
                id=uuid.uuid4(),
                merchant_id=merchant_id,
                source_id=source_id,
                source_product_id=sp_id,
                title=f"Product {gid.hex[:6]}",
                source_url="https://example.com/p",
                canonical_garment_id=gid,
                status="active",
            )
            mo = MerchantOffer(
                id=uuid.uuid4(),
                garment_id=gid,
                merchant_id=merchant_id,
                source_product_id=sp_id,
                url="https://example.com/p",
                price_minor=price,
                currency="INR",
                in_stock=True,
            )
            catalog_uow.session.add_all([mp, mo])

        # Add enrichments
        enr1 = GarmentEnrichment(
            garment_id=g1_id,
            model_version="1.0",
            embedding_model="mock-fake-512:mock-v1",
            attributes_json={"dominant_color": "navy", "silhouette": "regular", "formality": "casual"},
            embedding=[0.05] * 512,
        )
        enr2 = GarmentEnrichment(
            garment_id=g2_id,
            model_version="1.0",
            embedding_model="mock-fake-512:mock-v1",
            attributes_json={"dominant_color": "white", "silhouette": "slim", "formality": "casual"},
            embedding=[0.06] * 512,
        )
        enr3 = GarmentEnrichment(
            garment_id=g3_id,
            model_version="1.0",
            embedding_model="mock-fake-512:mock-v1",
            attributes_json={"dominant_color": "yellow", "silhouette": "regular", "formality": "casual"},
            embedding=[0.07] * 512,
        )
        catalog_uow.session.add_all([enr1, enr2, enr3])
        await catalog_uow.commit()

    # 3. Retrieve feed
    resp1 = api_client.get("/api/v1/feed", headers=headers)
    assert resp1.status_code == 200, resp1.text
    feed_data = resp1.json()
    returned_garment_ids = [item["garment_id"] for item in feed_data["items"]]

    # Yellow top should be filtered due to colors_avoided
    assert str(g3_id) not in returned_garment_ids
    assert str(g1_id) in returned_garment_ids
    assert str(g2_id) in returned_garment_ids

    # 4. Hide garment 1
    resp_sig = api_client.post(
        "/api/v1/feed/signals",
        json={"garment_id": str(g1_id), "action": "hide"},
        headers=headers,
    )
    assert resp_sig.status_code == 201

    # 5. Subsequent feed excludes g1
    resp2 = api_client.get("/api/v1/feed", headers=headers)
    assert resp2.status_code == 200
    feed_data_2 = resp2.json()
    new_ids = [item["garment_id"] for item in feed_data_2["items"]]

    assert str(g1_id) not in new_ids
    assert str(g2_id) in new_ids
