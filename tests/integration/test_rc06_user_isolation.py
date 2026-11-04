from uuid import UUID, uuid4
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from database.models import Base
from database.models.catalog import CanonicalGarment, Merchant, MerchantOffer
from database.models.identity import User
from fashx.api.v1.cart import router as cart_router
from fashx.api.v1.checkout import router as checkout_router
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
from fashx.core.database import get_session_factory
from fashx.core.dependencies import get_storage
from fashx.domain.cart.entities import Cart
from fashx.domain.cart.service import CartService
from fashx.domain.checkout.entities import CheckoutSession
from fashx.domain.checkout.service import CheckoutService
from fashx.gateway.errors import install_exception_handlers
from fashx.infrastructure.storage.local import LocalStorage
from fashx.profile.repositories.profile_repository import ProfileUnitOfWork
from fashx.security.deps import get_identity_repo
from fashx.security.errors import ApiError, api_error_handler
from fashx.security.identity import InMemoryIdentityRepo
from fashx.tryon.repositories.tryon_repository import TryOnUnitOfWork
from tests.conftest import make_token


@pytest.fixture
async def isolation_env(tmp_path):
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    storage = LocalStorage(root_dir=tmp_path / "iso_storage", base_url="http://storage.local")

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
    app.dependency_overrides[get_storage] = lambda: storage

    app.include_router(commerce_router, prefix="/api/v1")
    app.include_router(cart_router, prefix="/api/v1")
    app.include_router(checkout_router, prefix="/api/v1")

    client = TestClient(app)
    yield client, session_factory, repo
    await engine.dispose()


@pytest.mark.asyncio
async def test_rc06_wardrobe_user_isolation(isolation_env):
    client, session_factory, identity_repo = isolation_env

    identity_a = await identity_repo.resolve("fashx-test", "user-a")
    user_a = UUID(identity_a.user_id)
    identity_b = await identity_repo.resolve("fashx-test", "user-b")
    user_b = UUID(identity_b.user_id)
    garment_id = uuid4()
    merchant_id = uuid4()
    offer_id = uuid4()

    token_a = make_token(sub="user-a")
    token_b = make_token(sub="user-b")

    async with ProfileUnitOfWork(session_factory) as uow:
        uow.users.add(User(id=user_a))
        uow.users.add(User(id=user_b))
        await uow.commit()

    async with CatalogUnitOfWork(session_factory) as uow:
        uow.canonical_garments.add(
            CanonicalGarment(id=garment_id, display_name="Silk Scarf", category="accessories", active=True, price_minor=99900)
        )
        uow.merchants.add(Merchant(id=merchant_id, name="Shop", merchant_type="retailer"))
        uow.offers.add(
            MerchantOffer(
                id=offer_id,
                garment_id=garment_id,
                merchant_id=merchant_id,
                source_product_id="SCF-1",
                url="https://shop.com/scarf",
                price_minor=99900,
                currency="INR",
                in_stock=True,
            )
        )
        await uow.commit()

    # User A saves an item
    save_resp = client.post(
        "/api/v1/wardrobe/items",
        json={"garment_id": str(garment_id), "offer_id": str(offer_id)},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert save_resp.status_code == 201
    item_id = save_resp.json()["item_id"]

    # User B lists their wardrobe -> must NOT contain User A's item
    list_b = client.get("/api/v1/wardrobe/items", headers={"Authorization": f"Bearer {token_b}"})
    assert list_b.status_code == 200
    assert len(list_b.json()) == 0

    # User B attempts to access User A's wardrobe by user ID (legacy route RC06-T14)
    leak_resp = client.get(
        f"/api/v1/wardrobe/users/{user_a}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert leak_resp.status_code == 403

    # User B attempts to delete User A's wardrobe item
    del_resp = client.delete(
        f"/api/v1/wardrobe/users/{user_a}/items/{item_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert del_resp.status_code == 403


@pytest.mark.asyncio
async def test_rc06_cart_and_checkout_user_isolation(isolation_env):
    client, session_factory, identity_repo = isolation_env

    identity_a = await identity_repo.resolve("fashx-test", "alice")
    user_a = UUID(identity_a.user_id)
    identity_b = await identity_repo.resolve("fashx-test", "bob")
    user_b = UUID(identity_b.user_id)

    token_a = make_token(sub="alice")
    token_b = make_token(sub="bob")

    from fashx.api.v1.cart import get_cart_service
    from fashx.api.v1.checkout import get_checkout_service
    from fashx.core.context import CoreContext

    cart_svc = get_cart_service()
    checkout_svc = get_checkout_service()

    # Create Cart for User A
    cart_a = await cart_svc.create_cart(
        context=CoreContext.create(),
        cart=Cart(owner_type="customer", customer_id=user_a, currency="INR"),
    )

    # RC06-T19: User B attempts to read User A's cart -> 403 Forbidden
    resp = client.get(
        f"/api/v1/cart/{cart_a.id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert resp.status_code == 403
    assert "belongs to another user" in resp.json()["detail"]

    # User A CAN read their own cart
    resp_a = client.get(
        f"/api/v1/cart/{cart_a.id}",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert resp_a.status_code == 200

    # Create Checkout Session for User A
    checkout_a = await checkout_svc.create_checkout(
        context=CoreContext.create(),
        checkout=CheckoutSession(cart_id=cart_a.id, customer_id=user_a, currency="INR"),
    )

    # RC06-T20: User B attempts to validate User A's checkout -> 403 Forbidden
    resp_co = client.post(
        f"/api/v1/checkout/{checkout_a.id}/validate",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert resp_co.status_code == 403
    assert "belongs to another user" in resp_co.json()["detail"]
