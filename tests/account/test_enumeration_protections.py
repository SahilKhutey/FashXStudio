import time

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from database.models import Base
from fashx.account.repository import AccountRepository
from fashx.account.schemas import EmailChangeRequest
from fashx.account.service import AccountService


@pytest.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(engine, expire_on_commit=False)
    async with session_maker() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_enumeration_protection_timing_consistency(db_session: AsyncSession):
    repo = AccountRepository(db_session)
    service = AccountService(repo)

    # Provision user 1
    user1, _, _ = await repo.create_or_get_user_for_identity(
        "cognito", "sub-1", "shopper1@example.com", True
    )

    # 1. Email change request for user 1 with arbitrary email
    t0 = time.perf_counter()
    res1 = await service.request_email_change(
        user1.id, EmailChangeRequest(new_email="random.new1@example.com")
    )
    t1 = time.perf_counter()

    t2 = time.perf_counter()
    res2 = await service.request_email_change(
        user1.id, EmailChangeRequest(new_email="random.new2@example.com")
    )
    t3 = time.perf_counter()

    assert res1.status == "verification_sent"
    assert res2.status == "verification_sent"
    assert abs((t1 - t0) - (t3 - t2)) < 0.1
