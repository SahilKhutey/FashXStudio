from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession


@asynccontextmanager
async def transaction(session: AsyncSession) -> AsyncIterator[AsyncSession]:
    """Provide one explicit transaction boundary for an application use case."""
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
