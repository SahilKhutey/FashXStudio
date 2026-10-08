from abc import ABC, abstractmethod
from uuid import UUID

from .entities import (
    CancellationRequest,
    Refund,
    ReplacementRequest,
    ReturnLine,
    ReturnRequest,
)


class ReturnRepository(ABC):
    @abstractmethod
    async def get(
        self,
        return_id: UUID,
    ) -> ReturnRequest | None:
        raise NotImplementedError

    @abstractmethod
    async def save(
        self,
        request: ReturnRequest,
    ) -> ReturnRequest:
        raise NotImplementedError

    @abstractmethod
    async def list_by_order(
        self,
        order_id: UUID,
    ) -> list[ReturnRequest]:
        raise NotImplementedError


class ReturnLineRepository(ABC):
    @abstractmethod
    async def save(
        self,
        line: ReturnLine,
    ) -> ReturnLine:
        raise NotImplementedError

    @abstractmethod
    async def list_by_return(
        self,
        return_id: UUID,
    ) -> list[ReturnLine]:
        raise NotImplementedError


class CancellationRepository(ABC):
    @abstractmethod
    async def get(
        self,
        cancellation_id: UUID,
    ) -> CancellationRequest | None:
        raise NotImplementedError

    @abstractmethod
    async def save(
        self,
        cancellation: CancellationRequest,
    ) -> CancellationRequest:
        raise NotImplementedError

    @abstractmethod
    async def get_by_order(
        self,
        order_id: UUID,
    ) -> CancellationRequest | None:
        raise NotImplementedError


class RefundRepository(ABC):
    @abstractmethod
    async def get(
        self,
        refund_id: UUID,
    ) -> Refund | None:
        raise NotImplementedError

    @abstractmethod
    async def save(
        self,
        refund: Refund,
    ) -> Refund:
        raise NotImplementedError

    @abstractmethod
    async def list_by_order(
        self,
        order_id: UUID,
    ) -> list[Refund]:
        raise NotImplementedError


class ReplacementRepository(ABC):
    @abstractmethod
    async def get(
        self,
        replacement_id: UUID,
    ) -> ReplacementRequest | None:
        raise NotImplementedError

    @abstractmethod
    async def save(
        self,
        replacement: ReplacementRequest,
    ) -> ReplacementRequest:
        raise NotImplementedError
