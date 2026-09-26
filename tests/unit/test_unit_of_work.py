import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from api.app.core.unit_of_work import SqlAlchemyUnitOfWork
from database.models.identity import User


@pytest.mark.asyncio
async def test_uow_commit_persists_entity(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    uow = SqlAlchemyUnitOfWork(session_factory)

    async with uow:
        user = User()
        uow.session.add(user)
        await uow.commit()
        user_id = user.id

    # Verify persisted in a separate session
    async with session_factory() as session:
        fetched = await session.get(User, user_id)
        assert fetched is not None
        assert fetched.id == user_id


@pytest.mark.asyncio
async def test_uow_rollback_on_exception(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    uow = SqlAlchemyUnitOfWork(session_factory)

    with pytest.raises(ValueError):
        async with uow:
            user = User()
            uow.session.add(user)
            await uow.session.flush()
            user_id = user.id
            raise ValueError("Forced error inside transaction")

    # Verify NOT persisted
    async with session_factory() as session:
        fetched = await session.get(User, user_id)
        assert fetched is None


@pytest.mark.asyncio
async def test_uow_session_access_outside_context_raises(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    uow = SqlAlchemyUnitOfWork(session_factory)
    with pytest.raises(RuntimeError, match="UnitOfWork session is not active"):
        _ = uow.session
