from collections.abc import Sequence
from typing import Any

from database.models.base import Base
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class BaseRepository[T: Base]:
    """Generic async repository providing standard CRUD operations."""

    def __init__(self, session: AsyncSession, model_cls: type[T]) -> None:
        self.session = session
        self.model_cls = model_cls

    async def get_by_id(self, id_: Any) -> T | None:
        """Fetch entity by primary key using session.get."""
        return await self.session.get(self.model_cls, id_)

    async def list(self, limit: int = 100, offset: int = 0) -> Sequence[T]:
        """List entities with pagination."""
        stmt = select(self.model_cls).limit(limit).offset(offset)
        result = await self.session.scalars(stmt)
        return result.all()

    def add(self, entity: T) -> T:
        """Stage entity for insertion."""
        self.session.add(entity)
        return entity

    def add_all(self, entities: Sequence[T]) -> Sequence[T]:
        """Stage multiple entities for insertion."""
        self.session.add_all(entities)
        return entities

    async def delete(self, entity: T) -> None:
        """Stage entity for deletion."""
        await self.session.delete(entity)

    async def flush(self) -> None:
        """Flush pending changes to the database without committing the transaction."""
        await self.session.flush()
