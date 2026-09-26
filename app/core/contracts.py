from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Generic, TypeVar
from uuid import UUID

T = TypeVar("T")


class Entity(ABC):
    """
    Base contract for all persistent domain entities.
    """

    id: UUID
    created_at: datetime
    updated_at: datetime

    @abstractmethod
    def validate(self) -> None:
        """Validate entity invariants."""
        raise NotImplementedError


class Repository(Generic[T], ABC):
    """
    Persistence abstraction.

    Domain/services must depend on this contract,
    not directly on a database implementation.
    """

    @abstractmethod
    async def get(self, entity_id: UUID) -> T | None:
        raise NotImplementedError

    @abstractmethod
    async def save(self, entity: T) -> T:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, entity_id: UUID) -> None:
        raise NotImplementedError


class Service(ABC):
    """
    Base application service contract.
    """

    @abstractmethod
    async def execute(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError
