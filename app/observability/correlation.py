from contextvars import ContextVar
from uuid import UUID

_current_correlation_id: ContextVar[UUID | None] = ContextVar(
    "current_correlation_id",
    default=None,
)


def set_correlation_id(
    correlation_id: UUID | None,
) -> None:
    _current_correlation_id.set(correlation_id)


def get_correlation_id() -> UUID | None:
    return _current_correlation_id.get()
