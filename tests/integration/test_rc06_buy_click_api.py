from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from database.models import Base
from fashx.catalog.repositories.catalog_repository import CatalogUnitOfWork
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
from fashx.gateway.errors import install_exception_handlers
from fashx.profile.repositories.profile_repository import ProfileUnitOfWork
from fashx.security.deps import get_identity_repo
from fashx.security.errors import ApiError, api_error_handler
from fashx.security.identity import InMemoryIdentityRepo
from tests.conftest import make_token


@pytest.fixture
async def commerce_api_env():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    app = FastAPI()
    app.add_exception_handler(ApiError, api_error_handler)
    install_exception_handlers(app)
    repo = InMemoryIdentityRepo()

    app.dependency_overrides[get_identity_repo] = lambda: repo
    app.dependency_overrides[get_commerce_uow] = lambda: CommerceWardrobeUnitOfWork(session_factory)
    app.dependency_overrides[get_profile_uow] = lambda: ProfileUnitOfWork(session_factory)
    app.dependency_overrides[get_catalog_uow] = lambda: CatalogUnitOfWork(session_factory)

    app.include_router(commerce_router, prefix="/api/v1")
    client = TestClient(app)
    yield client, session_factory, repo
    await engine.dispose()


@pytest.mark.asyncio
async def test_rc06_buy_click_missing_offer_id_rejected(commerce_api_env):
    client, session_factory, identity_repo = commerce_api_env
    identity = await identity_repo.resolve("fashx-test", "test-user")
    user_id = UUID(identity.user_id)
    token = make_token(sub="test-user")

    # Calling buy-clicks without offer_id must fail with 422 Unprocessable Entity
    resp = client.post(
        "/api/v1/commerce/buy-clicks",
        json={"garment_id": str(uuid4())},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code in (400, 422)
    assert "offer_id" in resp.text


@pytest.mark.asyncio
async def test_rc06_buy_click_user_id_mismatch_rejected(commerce_api_env):
    client, session_factory, identity_repo = commerce_api_env
    identity = await identity_repo.resolve("fashx-test", "legit-user")
    user_id = UUID(identity.user_id)
    attacker_id = uuid4()

    token = make_token(sub="legit-user")

    # User attempts to submit someone else's user_id in the body
    resp = client.post(
        "/api/v1/commerce/buy-clicks",
        json={
            "garment_id": str(uuid4()),
            "offer_id": str(uuid4()),
            "user_id": str(attacker_id),
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403
    assert "user_id mismatch" in resp.json()["detail"]
