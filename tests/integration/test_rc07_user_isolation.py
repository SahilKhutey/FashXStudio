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
from fashx.catalog.router import get_catalog_uow
from fashx.main import app
from fashx.recommendation.router import get_profile_uow
from fashx.security.deps import get_identity_repo
from tests.conftest import make_token


@pytest.fixture
def api_client():
    return TestClient(app)


@pytest.mark.asyncio
async def test_cross_user_isolation_on_feed_and_signals(api_client: TestClient) -> None:
    repo = app.dependency_overrides[get_identity_repo]()
    id_a = await repo.resolve("fashx-test", "user-iso-test-a")
    id_b = await repo.resolve("fashx-test", "user-iso-test-b")
    user_a = uuid.UUID(id_a.user_id)
    user_b = uuid.UUID(id_b.user_id)

    token_a = make_token(sub="user-iso-test-a")
    token_b = make_token(sub="user-iso-test-b")
    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Ensure both users exist
    profile_uow = app.dependency_overrides[get_profile_uow]()
    async with profile_uow:
        profile_uow.users.add(User(id=user_a))
        profile_uow.users.add(User(id=user_b))
        await profile_uow.commit()

    # Seed shared catalog items
    catalog_uow = app.dependency_overrides[get_catalog_uow]()
    brand_id = uuid.uuid4()
    source_id = uuid.uuid4()
    merchant_id = uuid.uuid4()
    g1_id = uuid.uuid4()
    g2_id = uuid.uuid4()

    async with catalog_uow:
        catalog_uow.session.add(Brand(id=brand_id, name="Shared Brand", normalized_name=f"brand-{uuid.uuid4().hex[:6]}"))
        catalog_uow.session.add(
            CatalogSource(
                id=source_id,
                slug=f"source-{uuid.uuid4().hex[:6]}",
                name="Source Shared",
                kind="test",
                status="cleared",
                rights_display=True,
                rights_tryon=True,
            )
        )
        catalog_uow.session.add(Merchant(id=merchant_id, name="Merchant Shared", merchant_type="retailer"))

        g1 = CanonicalGarment(
            id=g1_id,
            brand_id=brand_id,
            display_name="Garment 1",
            category="tops",
            subcategory="shirt",
            gender="unisex",
            active=True,
            in_stock=True,
            price_minor=3000,
        )
        g2 = CanonicalGarment(
            id=g2_id,
            brand_id=brand_id,
            display_name="Garment 2",
            category="tops",
            subcategory="shirt",
            gender="unisex",
            active=True,
            in_stock=True,
            price_minor=3500,
        )
        catalog_uow.session.add_all([g1, g2])

        for gid in (g1_id, g2_id):
            sp_id = f"sp-{gid.hex[:6]}"
            catalog_uow.session.add(
                MerchantProduct(
                    id=uuid.uuid4(),
                    merchant_id=merchant_id,
                    source_id=source_id,
                    source_product_id=sp_id,
                    title="Product",
                    source_url="https://example.com",
                    canonical_garment_id=gid,
                    status="active",
                )
            )
            catalog_uow.session.add(
                MerchantOffer(
                    id=uuid.uuid4(),
                    garment_id=gid,
                    merchant_id=merchant_id,
                    source_product_id=sp_id,
                    url="https://example.com",
                    price_minor=3000,
                    currency="INR",
                    in_stock=True,
                )
            )
            catalog_uow.session.add(
                GarmentEnrichment(
                    garment_id=gid,
                    model_version="1.0",
                    embedding_model="mock-fake-512:mock-v1",
                    attributes_json={"dominant_color": "blue", "silhouette": "regular"},
                    embedding=[0.05] * 512,
                )
            )
        await catalog_uow.commit()

    # User A hides Garment 1
    resp_sig = api_client.post(
        "/api/v1/feed/signals",
        json={"garment_id": str(g1_id), "action": "hide"},
        headers=headers_a,
    )
    assert resp_sig.status_code == 201

    # Check User A feed: G1 excluded, G2 present
    resp_feed_a = api_client.get("/api/v1/feed", headers=headers_a)
    assert resp_feed_a.status_code == 200
    ids_a = [item["garment_id"] for item in resp_feed_a.json()["items"]]
    assert str(g1_id) not in ids_a
    assert str(g2_id) in ids_a

    # Check User B feed: BOTH G1 and G2 are present (User A's hide does not contaminate User B)
    resp_feed_b = api_client.get("/api/v1/feed", headers=headers_b)
    assert resp_feed_b.status_code == 200
    ids_b = [item["garment_id"] for item in resp_feed_b.json()["items"]]
    assert str(g1_id) in ids_b
    assert str(g2_id) in ids_b
