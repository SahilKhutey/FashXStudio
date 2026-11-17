
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from database.models import Base
from fashx.account.repository import AccountRepository
from fashx.account.schemas import AccountProvisionRequest, AccountStatus
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
async def test_idempotent_account_provisioning(db_session: AsyncSession):
    repo = AccountRepository(db_session)
    service = AccountService(repo)

    sub = "cognito-sub-12345"
    req1 = AccountProvisionRequest(
        email="Shopper.One@Example.COM",
        email_verified=True,
    )

    # 1. First provision: creates new user
    res1 = await service.provision_account("cognito", sub, req1)
    assert res1.is_new is True
    assert res1.email_normalized == "shopper.one@example.com"
    assert res1.status == AccountStatus.ACTIVE
    assert res1.email_verified is True

    # 2. Second provision: idempotent, returns same user_id and is_new=False
    req2 = AccountProvisionRequest(
        email="Shopper.One@Example.COM",
        email_verified=True,
    )
    res2 = await service.provision_account("cognito", sub, req2)
    assert res2.is_new is False
    assert res2.user_id == res1.user_id
    assert res2.status == AccountStatus.ACTIVE


@pytest.mark.asyncio
async def test_unverified_provisioning_and_reconciliation(db_session: AsyncSession):
    repo = AccountRepository(db_session)
    service = AccountService(repo)

    sub = "cognito-sub-unverified-1"
    req_unverified = AccountProvisionRequest(
        email="unverified@fashx.com",
        email_verified=False,
    )

    # 1. Unverified creates PENDING_VERIFICATION
    res1 = await service.provision_account("cognito", sub, req_unverified)
    assert res1.is_new is True
    assert res1.status == AccountStatus.PENDING_VERIFICATION
    assert res1.email_verified is False

    # 2. Subsequent call after verification reconciles to ACTIVE
    req_verified = AccountProvisionRequest(
        email="unverified@fashx.com",
        email_verified=True,
    )
    res2 = await service.provision_account("cognito", sub, req_verified)
    assert res2.is_new is False
    assert res2.user_id == res1.user_id
    assert res2.status == AccountStatus.ACTIVE
    assert res2.email_verified is True
