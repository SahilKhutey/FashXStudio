import asyncio

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from database.models import Base
from fashx.api.v1.me import get_profile_uow
from fashx.api.v1.me import router as me_router
from fashx.profile.repositories.profile_repository import ProfileUnitOfWork
from fashx.security.deps import get_identity_repo
from fashx.security.errors import ApiError, api_error_handler
from fashx.security.identity import InMemoryIdentityRepo
from tests.conftest import make_token


@pytest.fixture
def me_client():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
    )

    async def _init_db():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    asyncio.run(_init_db())
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    app = FastAPI()
    app.add_exception_handler(ApiError, api_error_handler)
    repo = InMemoryIdentityRepo()
    app.dependency_overrides[get_identity_repo] = lambda: repo
    app.dependency_overrides[get_profile_uow] = lambda: ProfileUnitOfWork(session_factory)
    app.include_router(me_router)
    yield TestClient(app), repo
    asyncio.run(engine.dispose())


def test_get_me_unauthenticated(me_client):
    client, _ = me_client
    response = client.get("/me")
    assert response.status_code == 401


def test_get_me_authenticated(me_client):
    client, _ = me_client
    token = make_token(sub="test-user")
    response = client.get("/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert "user_id" in data
    assert data["roles"] == ["user"]
