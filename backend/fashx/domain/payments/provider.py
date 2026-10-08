from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class ProviderPaymentResult:
    success: bool
    provider_payment_id: str | None = None
    provider_transaction_id: str | None = None
    requires_action: bool = False
    error_code: str | None = None
    error_message: str | None = None


class PaymentProvider(ABC):
    @abstractmethod
    async def authorize(
        self,
        *,
        amount: Decimal,
        currency: str,
        payment_method: str,
        metadata: dict[str, str],
    ) -> ProviderPaymentResult:
        raise NotImplementedError

    @abstractmethod
    async def capture(
        self,
        *,
        provider_payment_id: str,
        amount: Decimal,
        currency: str,
    ) -> ProviderPaymentResult:
        raise NotImplementedError

    @abstractmethod
    async def cancel(
        self,
        *,
        provider_payment_id: str,
    ) -> ProviderPaymentResult:
        raise NotImplementedError


class TestPaymentProvider(PaymentProvider):
    async def authorize(
        self,
        *,
        amount: Decimal,
        currency: str,
        payment_method: str,
        metadata: dict[str, str],
    ) -> ProviderPaymentResult:
        return ProviderPaymentResult(
            success=True,
            provider_payment_id="test-payment",
            provider_transaction_id="test-auth",
        )

    async def capture(
        self,
        *,
        provider_payment_id: str,
        amount: Decimal,
        currency: str,
    ) -> ProviderPaymentResult:
        return ProviderPaymentResult(
            success=True,
            provider_payment_id=provider_payment_id,
            provider_transaction_id="test-capture",
        )

    async def cancel(
        self,
        *,
        provider_payment_id: str,
    ) -> ProviderPaymentResult:
        return ProviderPaymentResult(
            success=True,
            provider_payment_id=provider_payment_id,
        )
