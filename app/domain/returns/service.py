from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.core.context import CoreContext
from app.core.errors import NotFoundError
from app.core.event_bus import EventBus

from .entities import (
    CancellationRequest,
    Refund,
    ReplacementRequest,
    ReturnLine,
    ReturnRequest,
)
from .enums import (
    CancellationStatus,
    RefundStatus,
    ReturnStatus,
)
from .events import (
    CancellationCompleted,
    CancellationRequested,
    RefundCompleted,
    RefundFailed,
    RefundRequested,
    ReplacementRequested,
    ReturnAccepted,
    ReturnRejected,
    ReturnRequested,
)
from .lifecycle import (
    CANCELLATION_TRANSITIONS,
    REFUND_TRANSITIONS,
    RETURN_TRANSITIONS,
    validate_transition,
)
from .repository import (
    CancellationRepository,
    RefundRepository,
    ReplacementRepository,
    ReturnLineRepository,
    ReturnRepository,
)


@dataclass(slots=True)
class ReturnsService:
    return_repository: ReturnRepository
    return_line_repository: ReturnLineRepository
    cancellation_repository: CancellationRepository
    refund_repository: RefundRepository
    replacement_repository: ReplacementRepository
    event_bus: EventBus

    async def request_return(
        self,
        *,
        context: CoreContext,
        request: ReturnRequest,
        lines: list[ReturnLine],
    ) -> ReturnRequest:
        request.validate()

        for line in lines:
            line.return_id = request.id
            line.validate()
            await self.return_line_repository.save(line)

        await self.return_repository.save(request)

        await self.event_bus.publish(
            ReturnRequested(
                entity_id=request.id,
                correlation_id=context.correlation_id,
            )
        )

        return request

    async def get_return(
        self,
        return_id: UUID,
    ) -> ReturnRequest:
        result = await self.return_repository.get(return_id)
        if result is None:
            raise NotFoundError(
                "Return request was not found.",
                {"return_id": str(return_id)},
            )
        return result

    async def change_return_status(
        self,
        *,
        context: CoreContext,
        return_id: UUID,
        target: ReturnStatus,
    ) -> ReturnRequest:
        request = await self.get_return(return_id)

        validate_transition(
            request.status,
            target,
            RETURN_TRANSITIONS,
            "return",
        )

        request.status = target
        request.touch()

        await self.return_repository.save(request)

        if target == ReturnStatus.ACCEPTED:
            await self.event_bus.publish(
                ReturnAccepted(
                    entity_id=request.id,
                    correlation_id=context.correlation_id,
                )
            )
        elif target == ReturnStatus.REJECTED:
            await self.event_bus.publish(
                ReturnRejected(
                    entity_id=request.id,
                    correlation_id=context.correlation_id,
                )
            )

        return request

    async def request_cancellation(
        self,
        *,
        context: CoreContext,
        request: CancellationRequest,
    ) -> CancellationRequest:
        request.validate()

        await self.cancellation_repository.save(request)

        await self.event_bus.publish(
            CancellationRequested(
                entity_id=request.id,
                correlation_id=context.correlation_id,
            )
        )

        return request

    async def change_cancellation_status(
        self,
        *,
        context: CoreContext,
        cancellation_id: UUID,
        target: CancellationStatus,
    ) -> CancellationRequest:
        cancellation = await self.cancellation_repository.get(cancellation_id)

        if cancellation is None:
            raise NotFoundError(
                "Cancellation was not found.",
                {"cancellation_id": str(cancellation_id)},
            )

        validate_transition(
            cancellation.status,
            target,
            CANCELLATION_TRANSITIONS,
            "cancellation",
        )

        cancellation.status = target
        cancellation.touch()

        await self.cancellation_repository.save(cancellation)

        if target == CancellationStatus.COMPLETED:
            await self.event_bus.publish(
                CancellationCompleted(
                    entity_id=cancellation.id,
                    correlation_id=context.correlation_id,
                )
            )

        return cancellation

    async def request_refund(
        self,
        *,
        context: CoreContext,
        refund: Refund,
    ) -> Refund:
        refund.validate()

        await self.refund_repository.save(refund)

        await self.event_bus.publish(
            RefundRequested(
                entity_id=refund.id,
                correlation_id=context.correlation_id,
            )
        )

        return refund

    async def change_refund_status(
        self,
        *,
        context: CoreContext,
        refund_id: UUID,
        target: RefundStatus,
    ) -> Refund:
        refund = await self.refund_repository.get(refund_id)

        if refund is None:
            raise NotFoundError(
                "Refund was not found.",
                {"refund_id": str(refund_id)},
            )

        validate_transition(
            refund.status,
            target,
            REFUND_TRANSITIONS,
            "refund",
        )

        refund.status = target
        refund.touch()

        await self.refund_repository.save(refund)

        if target == RefundStatus.COMPLETED:
            await self.event_bus.publish(
                RefundCompleted(
                    entity_id=refund.id,
                    correlation_id=context.correlation_id,
                )
            )
        elif target == RefundStatus.FAILED:
            await self.event_bus.publish(
                RefundFailed(
                    entity_id=refund.id,
                    correlation_id=context.correlation_id,
                )
            )

        return refund

    async def request_replacement(
        self,
        *,
        context: CoreContext,
        replacement: ReplacementRequest,
    ) -> ReplacementRequest:
        replacement.validate()

        await self.replacement_repository.save(replacement)

        await self.event_bus.publish(
            ReplacementRequested(
                entity_id=replacement.id,
                correlation_id=context.correlation_id,
            )
        )

        return replacement
