from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from database.models import Base
from fashx.account.repository import AccountRepository


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
async def test_concurrent_sessions_recording_and_revocation(db_session: AsyncSession):
    repo = AccountRepository(db_session)

    # 1. Create a user
    user, _, _ = await repo.create_or_get_user_for_identity(
        provider="cognito",
        provider_subject="shopper-device-test",
        email="device.test@fashx.com",
        email_verified=True,
    )

    now = datetime.now(UTC)
    expires = now + timedelta(hours=1)

    # 2. Record multiple sessions (e.g. iPhone and iPad)
    session1 = await repo.record_session(
        user_id=user.id,
        provider="cognito",
        provider_jti="jti-iphone-123",
        expires_at=expires,
        device_label="iPhone 15 Pro",
    )
    assert session1.session_status == "ACTIVE"
    assert session1.device_label == "iPhone 15 Pro"

    session2 = await repo.record_session(
        user_id=user.id,
        provider="cognito",
        provider_jti="jti-ipad-456",
        expires_at=expires,
        device_label="iPad Air",
    )
    assert session2.session_status == "ACTIVE"
    assert session2.device_label == "iPad Air"

    # 3. Global logout: revoke all sessions
    revoked_count = await repo.revoke_all_sessions(
        user_id=user.id,
        subject="shopper-device-test",
        provider="cognito",
    )
    assert revoked_count == 2

    # 4. Refresh session objects and verify REVOKED status
    await db_session.refresh(session1)
    await db_session.refresh(session2)
    assert session1.session_status == "REVOKED"
    assert session1.revoked_at is not None
    assert session2.session_status == "REVOKED"
    assert session2.revoked_at is not None
