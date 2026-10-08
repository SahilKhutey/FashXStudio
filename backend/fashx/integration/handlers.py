from __future__ import annotations

from .contracts import (
    IntegrationHandler,
    IntegrationMessage,
)


class LoggingIntegrationHandler(IntegrationHandler):
    def __init__(self, name: str = "generic_logger") -> None:
        self.name = name
        self.handled_messages: list[IntegrationMessage] = []

    async def handle(
        self,
        message: IntegrationMessage,
    ) -> None:
        self.handled_messages.append(message)


class OrderCompletedIntegrationHandler(IntegrationHandler):
    def __init__(self) -> None:
        self.processed_orders: list[IntegrationMessage] = []

    async def handle(
        self,
        message: IntegrationMessage,
    ) -> None:
        self.processed_orders.append(message)


class PaymentCapturedIntegrationHandler(IntegrationHandler):
    def __init__(self) -> None:
        self.captured_payments: list[IntegrationMessage] = []

    async def handle(
        self,
        message: IntegrationMessage,
    ) -> None:
        self.captured_payments.append(message)
