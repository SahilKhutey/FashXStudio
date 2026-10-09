from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from database.models import Base
from database.models.identity import User
from fashx.profile.repositories.profile_repository import ProfileUnitOfWork


@pytest_asyncio.fixture
async def session_factory() -> async_sessionmaker[AsyncSession]:
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    yield factory
    await engine.dispose()


@pytest.mark.asyncio
async def test_profile_uow_roundtrip_and_isolation(session_factory) -> None:
    uow = ProfileUnitOfWork(session_factory)
    user_a = uuid4()
    user_b = uuid4()

    async with uow:
        uow.users.add(User(id=user_a))
        uow.users.add(User(id=user_b))
        await uow.body_profiles.upsert(user_id=user_a, height_cm=175, weight_kg=70, build="athletic")
        await uow.body_profiles.upsert(user_id=user_b, height_cm=160, weight_kg=55, build="petite")
        await uow.preferences.upsert(user_id=user_a, colors_favored=["navy", "black"])
        await uow.commit()

    verify_uow = ProfileUnitOfWork(session_factory)
    async with verify_uow:
        body_a = await verify_uow.body_profiles.get_by_user_id(user_a)
        body_b = await verify_uow.body_profiles.get_by_user_id(user_b)
        assert body_a is not None
        assert body_a.height_cm == 175
        assert body_b is not None
        assert body_b.height_cm == 160

        pref_a = await verify_uow.preferences.get_by_user_id(user_a)
        assert pref_a is not None
        assert "navy" in pref_a.colors_favored

        # Missing user lookup returns None
        missing = await verify_uow.body_profiles.get_by_user_id(uuid4())
        assert missing is None
