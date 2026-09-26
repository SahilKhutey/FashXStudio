from __future__ import annotations

from collections import defaultdict

from app.core.errors import DependencyError

from .contracts import (
    IntegrationHandler,
    IntegrationMessage,
)


class IntegrationDispatcher:
    def __init__(self) -> None:
        self._handlers: dict[
            type,
            list[IntegrationHandler],
        ] = defaultdict(list)

    def register(
        self,
        event_type: type,
        handler: IntegrationHandler,
    ) -> None:
        self._handlers[event_type].append(handler)

    async def dispatch(
        self,
        message: IntegrationMessage,
    ) -> None:
        handlers = self._handlers.get(
            type(message.event),
            [],
        )

        for handler in handlers:
            try:
                await handler.handle(message)
            except Exception as exc:
                raise DependencyError(
                    "Integration handler failed.",
                    details={
                        "event": type(message.event).__name__,
                        "handler": type(handler).__name__,
                        "error": str(exc),
                    },
                ) from exc
