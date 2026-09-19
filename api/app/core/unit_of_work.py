from collections.abc import Callable
from types import TracebackType
from typing import Protocol, Self

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from .database import get_session_factory


class UnitOfWork(Protocol):
    """Protocol defining the Unit of Work lifecycle for transactional boundaries."""

    async def __aenter__(self) -> Self: ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None: ...

    async def commit(self) -> None: ...

    async def rollback(self) -> None: ...

    async def flush(self) -> None: ...


class SqlAlchemyUnitOfWork:
    """SQLAlchemy 2.x implementation of Unit of Work pattern."""

    def __init__(
        self,
        session_factory: (
            Callable[[], AsyncSession] | async_sessionmaker[AsyncSession] | None
        ) = None,
    ) -> None:
        self._session_factory = session_factory or get_session_factory()
        self._session: AsyncSession | None = None
        self._committed = False

    @property
    def session(self) -> AsyncSession:
        if self._session is None:
            raise RuntimeError(
                "UnitOfWork session is not active. Use within an 'async with' context."
            )
        return self._session

    async def __aenter__(self) -> Self:
        self._session = self._session_factory()
        self._committed = False
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if self._session is not None:
            try:
                if exc_type is not None or not self._committed:
                    await self.rollback()
            finally:
                await self._session.close()
                self._session = None

    async def commit(self) -> None:
        if self._session is not None:
            await self._session.commit()
            self._committed = True

    async def rollback(self) -> None:
        if self._session is not None:
            await self._session.rollback()

    async def flush(self) -> None:
        if self._session is not None:
            await self._session.flush()
