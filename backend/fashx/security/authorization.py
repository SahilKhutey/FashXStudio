from dataclasses import dataclass

from fashx.core.errors import ConflictError


@dataclass(frozen=True, slots=True)
class Actor:
    actor_id: str
    roles: frozenset[str]


def require_role(
    actor: Actor,
    role: str,
) -> None:
    if role not in actor.roles:
        raise ConflictError(
            "Actor is not authorized for this operation."
        )
