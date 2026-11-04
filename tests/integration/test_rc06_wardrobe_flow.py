from uuid import UUID, uuid4
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from database.models import Base
from database.models.catalog import CanonicalGarment, Merchant, MerchantOffer, MerchantProduct
from database.models.identity import User
from fashx.catalog.repositories.catalog_repository import CatalogUnitOfWork
from fashx.commerce_wardrobe.repositories.commerce_wardrobe_repository import (
    CommerceWardrobeUnitOfWork,
)
from fashx.commerce_wardrobe.router import (
    get_catalog_uow,
    get_commerce_uow,
    get_profile_uow,
    get_tryon_uow,
    router as commerce_router,
)
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
async def wardrobe_env(tmp_path):
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    storage = LocalStorage(root_dir=tmp_path / "wardrobe_storage", base_url="http://storage.local")

    app = FastAPI()
    app.add_exception_handler(ApiError, api_error_handler)
    install_exception_handlers(app)
    repo = InMemoryIdentityRepo()

    app.dependency_overrides[get_identity_repo] = lambda: repo
    app.dependency_overrides[get_commerce_uow] = lambda: CommerceWardrobeUnitOfWork(session_factory)
    app.dependency_overrides[get_profile_uow] = lambda: ProfileUnitOfWork(session_factory)
    app.dependency_overrides[get_catalog_uow] = lambda: CatalogUnitOfWork(session_factory)
    app.dependency_overrides[get_tryon_uow] = lambda: TryOnUnitOfWork(session_factory)
    app.dependency_overrides[get_storage] = lambda: storage

    app.include_router(commerce_router, prefix="/api/v1")
    client = TestClient(app)
    yield client, session_factory, repo
    await engine.dispose()


@pytest.mark.asyncio
async def test_rc06_wardrobe_save_list_remove_lifecycle(wardrobe_env):
    client, session_factory, identity_repo = wardrobe_env
    identity = await identity_repo.resolve("fashx-test", "wardrobe-user")
    user_id = UUID(identity.user_id)
    garment_id = uuid4()
    merchant_id = uuid4()
    offer_id = uuid4()

    token = make_token(sub="wardrobe-user")
    auth_headers = {"Authorization": f"Bearer {token}"}

    async with ProfileUnitOfWork(session_factory) as uow:
        uow.users.add(User(id=user_id))
        await uow.commit()

    async with CatalogUnitOfWork(session_factory) as uow:
        uow.canonical_garments.add(
            CanonicalGarment(
                id=garment_id,
                display_name="Tailored Blazer",
                category="outerwear",
                active=True,
                price_minor=599900,
            )
        )
        uow.merchants.add(Merchant(id=merchant_id, name="Boutique", merchant_type="retailer"))
        uow.merchant_products.add(
            MerchantProduct(
                id=uuid4(),
                merchant_id=merchant_id,
                source_product_id="BLZ-01",
                title="Tailored Blazer",
                source_url="https://boutique.com/blazer",
            )
        )
        uow.offers.add(
            MerchantOffer(
                id=offer_id,
                garment_id=garment_id,
                merchant_id=merchant_id,
                source_product_id="BLZ-01",
                url="https://boutique.com/blazer",
                price_minor=599900,
                currency="INR",
                in_stock=True,
            )
        )
        await uow.commit()

    # 1. Save to wardrobe
    save_resp = client.post(
        "/api/v1/wardrobe/items",
        json={"garment_id": str(garment_id), "offer_id": str(offer_id)},
        headers=auth_headers,
    )
    assert save_resp.status_code == 201
    item_id = save_resp.json()["item_id"]

    # 2. List wardrobe
    list_resp = client.get("/api/v1/wardrobe/items", headers=auth_headers)
    assert list_resp.status_code == 200
    items = list_resp.json()
    assert len(items) == 1
    assert items[0]["item_id"] == item_id
    assert items[0]["snapshot_title"] == "Tailored Blazer"

    # 3. Remove from wardrobe
    del_resp = client.delete(f"/api/v1/wardrobe/items/{item_id}", headers=auth_headers)
    assert del_resp.status_code == 204

    # 4. Verify list is empty
    list_after = client.get("/api/v1/wardrobe/items", headers=auth_headers)
    assert list_after.status_code == 200
    assert len(list_after.json()) == 0
