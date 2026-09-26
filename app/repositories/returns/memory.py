from uuid import UUID

from app.domain.returns.entities import (
    CancellationRequest,
    Refund,
    ReplacementRequest,
    ReturnLine,
    ReturnRequest,
)
from app.domain.returns.repository import (
    CancellationRepository,
    RefundRepository,
    ReplacementRepository,
    ReturnLineRepository,
    ReturnRepository,
)


class InMemoryReturnRepository(ReturnRepository):
    def __init__(self) -> None:
        self._items: dict[UUID, ReturnRequest] = {}

    async def get(self, return_id: UUID) -> ReturnRequest | None:
        return self._items.get(return_id)

    async def save(self, request: ReturnRequest) -> ReturnRequest:
        self._items[request.id] = request
        return request

    async def list_by_order(self, order_id: UUID) -> list[ReturnRequest]:
        return [
            item
            for item in self._items.values()
            if item.order_id == order_id
        ]


class InMemoryReturnLineRepository(ReturnLineRepository):
    def __init__(self) -> None:
        self._items: dict[UUID, ReturnLine] = {}

    async def save(self, line: ReturnLine) -> ReturnLine:
        self._items[line.id] = line
        return line

    async def list_by_return(self, return_id: UUID) -> list[ReturnLine]:
        return [
            item
            for item in self._items.values()
            if item.return_id == return_id
        ]


class InMemoryCancellationRepository(CancellationRepository):
    def __init__(self) -> None:
        self._items: dict[UUID, CancellationRequest] = {}

    async def get(self, cancellation_id: UUID) -> CancellationRequest | None:
        return self._items.get(cancellation_id)

    async def save(
        self, cancellation: CancellationRequest
    ) -> CancellationRequest:
        self._items[cancellation.id] = cancellation
        return cancellation

    async def get_by_order(
        self, order_id: UUID
    ) -> CancellationRequest | None:
        for item in self._items.values():
            if item.order_id == order_id:
                return item
        return None


class InMemoryRefundRepository(RefundRepository):
    def __init__(self) -> None:
        self._items: dict[UUID, Refund] = {}

    async def get(self, refund_id: UUID) -> Refund | None:
        return self._items.get(refund_id)

    async def save(self, refund: Refund) -> Refund:
        self._items[refund.id] = refund
        return refund

    async def list_by_order(self, order_id: UUID) -> list[Refund]:
        return [
            item
            for item in self._items.values()
            if item.order_id == order_id
        ]


class InMemoryReplacementRepository(ReplacementRepository):
    def __init__(self) -> None:
        self._items: dict[UUID, ReplacementRequest] = {}

    async def get(
        self, replacement_id: UUID
    ) -> ReplacementRequest | None:
        return self._items.get(replacement_id)

    async def save(
        self, replacement: ReplacementRequest
    ) -> ReplacementRequest:
        self._items[replacement.id] = replacement
        return replacement
