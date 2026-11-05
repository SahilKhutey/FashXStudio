from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from database.models import Base
from database.models.catalog import (
    CanonicalGarment,
    CatalogSource,
    Merchant,
    MerchantOffer,
    MerchantProduct,
)
from database.models.identity import User
from fashx.catalog.customer_router import customer_garment_router
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
    get_profile_uow,
    get_tryon_uow,
)
from fashx.commerce_wardrobe.router import (
    router as commerce_router,
)
from fashx.core.database import get_session_factory
from fashx.core.dependencies import get_storage
from fashx.gateway.errors import install_exception_handlers
from fashx.infrastructure.storage.local import LocalStorage
from fashx.profile.repositories.profile_repository import ProfileUnitOfWork
from fashx.security.deps import get_identity_repo
from fashx.security.errors import ApiError, api_error_handler
from fashx.security.identity import InMemoryIdentityRepo
from fashx.tryon.repositories.tryon_repository import TryOnUnitOfWork
from tests.conftest import make_token


@pytest.fixture
async def shopping_environment(tmp_path):
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    storage = LocalStorage(root_dir=tmp_path / "storage", base_url="http://storage.local")

    app = FastAPI()
    app.add_exception_handler(ApiError, api_error_handler)
    install_exception_handlers(app)
    repo = InMemoryIdentityRepo()

    app.dependency_overrides[get_identity_repo] = lambda: repo
    app.dependency_overrides[get_commerce_uow] = lambda: CommerceWardrobeUnitOfWork(session_factory)
    app.dependency_overrides[get_profile_uow] = lambda: ProfileUnitOfWork(session_factory)
    app.dependency_overrides[get_catalog_uow] = lambda: CatalogUnitOfWork(session_factory)
    app.dependency_overrides[get_commerce_catalog_uow] = lambda: CatalogUnitOfWork(session_factory)
    app.dependency_overrides[get_tryon_uow] = lambda: TryOnUnitOfWork(session_factory)
    app.dependency_overrides[get_session_factory] = lambda: session_factory
    app.dependency_overrides[get_storage] = lambda: storage

    app.include_router(customer_garment_router, prefix="/api/v1")
    app.include_router(commerce_router, prefix="/api/v1")

    client = TestClient(app)
    yield client, session_factory, repo
    await engine.dispose()


@pytest.mark.asyncio
async def test_rc06_complete_shopping_journey(shopping_environment):
    client, session_factory, identity_repo = shopping_environment

    # 1. Setup user identity
    identity = await identity_repo.resolve("fashx-test", "shopping-user")
    user_id = UUID(identity.user_id)
    token = make_token(sub="shopping-user")
    auth_headers = {"Authorization": f"Bearer {token}"}

    garment_id = uuid4()
    merchant_id = uuid4()
    source_id = uuid4()
    offer_id = uuid4()

    # 2. Seed catalog data
    async with ProfileUnitOfWork(session_factory) as uow:
        uow.users.add(User(id=user_id))
        await uow.commit()

    async with CatalogUnitOfWork(session_factory) as uow:
        uow.merchants.add(Merchant(id=merchant_id, name="Myntra Exclusive", merchant_type="retailer"))
        source = CatalogSource(
            id=source_id,
            slug="myntra-fashion",
            name="Myntra Cleared Feed",
            kind="manual",
            status="cleared",
            rights_display=True,
            rights_tryon=True,
            image_policy="mirror",
        )
        uow.sources.add(source)
        uow.canonical_garments.add(
            CanonicalGarment(
                id=garment_id,
                display_name="Relaxed Cuban Collar Shirt",
                category="tops",
                subcategory="shirts",
                active=True,
                price_minor=199900,
                sizes_in_stock=["M", "L", "XL"],
                tryon_supported=True,
            )
        )
        uow.merchant_products.add(
            MerchantProduct(
                id=uuid4(),
                merchant_id=merchant_id,
                source_id=source_id,
                source_product_id="MYN-SHIRT-01",
                title="Relaxed Cuban Collar Shirt Navy",
                source_url="https://www.myntra.com/shirts/relaxed-cuban-navy",
            )
        )
        uow.offers.add(
            MerchantOffer(
                id=offer_id,
                garment_id=garment_id,
                merchant_id=merchant_id,
                source_product_id="MYN-SHIRT-01",
                url="https://www.myntra.com/shirts/relaxed-cuban-navy",
                price_minor=199900,
                currency="INR",
                in_stock=True,
            )
        )
        await uow.commit()

    # Step A: Customer discovers garment details
    resp = client.get(f"/api/v1/garments/{garment_id}", headers=auth_headers)
    assert resp.status_code == 200
    garment_data = resp.json()
    assert garment_data["id"] == str(garment_id)
    assert garment_data["title"] == "Relaxed Cuban Collar Shirt"
    assert garment_data["price_minor"] == 199900
    assert garment_data["sizes_in_stock"] == ["M", "L", "XL"]
    assert garment_data["tryon_supported"] is True
    assert len(garment_data["offers"]) == 1
    assert garment_data["offers"][0]["id"] == str(offer_id)
    assert garment_data["offers"][0]["merchant_name"] == "Myntra Exclusive"
    assert garment_data["offers"][0]["in_stock"] is True

    # Step B: User initiates buy-click on selected offer
    buy_resp = client.post(
        "/api/v1/commerce/buy-clicks",
        json={"garment_id": str(garment_id), "offer_id": str(offer_id)},
        headers=auth_headers,
    )
    print("BUY ERROR DETAIL:", buy_resp.status_code, buy_resp.text)
    assert buy_resp.status_code == 201
    buy_data = buy_resp.json()
    assert "buy_click_id" in buy_data
    assert "redirect_url" in buy_data
    assert "tracking_id" in buy_data
    assert "utm_source=fashx" in buy_data["redirect_url"]
    assert "utm_campaign=vto_purchase" in buy_data["redirect_url"]
    assert buy_data["redirect_url"].startswith("https://www.myntra.com/shirts/relaxed-cuban-navy")

    # Step C: User saves product to wardrobe
    save_resp = client.post(
        "/api/v1/wardrobe/items",
        json={"garment_id": str(garment_id), "offer_id": str(offer_id)},
        headers=auth_headers,
    )
    assert save_resp.status_code == 201
    saved_data = save_resp.json()
    assert saved_data["garment_id"] == str(garment_id)
    assert saved_data["snapshot_title"] == "Relaxed Cuban Collar Shirt Navy"
    assert saved_data["snapshot_price_minor"] == 199900
    assert saved_data["snapshot_currency"] == "INR"

    # Step D: User lists wardrobe items
    list_resp = client.get("/api/v1/wardrobe/items", headers=auth_headers)
    assert list_resp.status_code == 200
    items = list_resp.json()
    assert len(items) >= 1
    assert any(item["garment_id"] == str(garment_id) for item in items)
