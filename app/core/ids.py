from __future__ import annotations

from uuid import UUID, uuid4


def new_id() -> UUID:
    """Create a new system entity identifier."""
    return uuid4()


def parse_id(value: str | UUID) -> UUID:
    """Validate and normalize an entity identifier."""
    if isinstance(value, UUID):
        return value

    return UUID(value)
