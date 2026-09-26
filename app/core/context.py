from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID, uuid4


@dataclass(frozen=True, slots=True)
class CoreContext:
    """
    Execution context shared across Core services.
    """

    request_id: UUID
    correlation_id: UUID
    actor_id: UUID | None = None

    @classmethod
    def create(
        cls,
        *,
        actor_id: UUID | None = None,
        correlation_id: UUID | None = None,
    ) -> CoreContext:
        return cls(
            request_id=uuid4(),
            correlation_id=correlation_id or uuid4(),
            actor_id=actor_id,
        )
