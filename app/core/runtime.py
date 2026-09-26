from __future__ import annotations

from dataclasses import dataclass, field

from .event_bus import EventBus
from .registry import CoreRegistry


@dataclass(slots=True)
class CoreRuntime:
    """
    Runtime composition root for Core systems.
    """

    registry: CoreRegistry = field(default_factory=CoreRegistry)
    event_bus: EventBus = field(default_factory=EventBus)

    @classmethod
    def create(cls) -> CoreRuntime:
        return cls(
            registry=CoreRegistry(),
            event_bus=EventBus(),
        )


_runtime: CoreRuntime | None = None


def get_core_runtime() -> CoreRuntime:
    global _runtime

    if _runtime is None:
        _runtime = CoreRuntime.create()

    return _runtime


def reset_core_runtime() -> None:
    global _runtime
    _runtime = None
