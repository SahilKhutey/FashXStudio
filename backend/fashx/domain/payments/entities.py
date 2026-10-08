from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from app.core.errors import ValidationError
from app.core.ids import new_id

from .enums import (
    PaymentMethodType,
    PaymentStatus,
    TransactionStatus,
    TransactionType,
)


def utc_now() -> datetime:
    return datetime.now(UTC)


@dataclass(slots=True)
class Payment:
    id: UUID = field(default_factory=new_id)
    order_id: UUID | None = None
    amount: Decimal = Decimal("0")
    currency: str = "INR"
    status: PaymentStatus = PaymentStatus.CREATED
    method: PaymentMethodType = PaymentMethodType.UPI
    provider: str = "internal"
    provider_payment_id: str | None = None
    idempotency_key: str | None = None
    metadata: dict[str, str] = field(default_factory=dict)
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)
    version: int = 1

    def validate(self) -> None:
        if self.order_id is None:
            raise ValidationError("Payment requires order ID.")

        if self.amount <= Decimal("0"):
            raise ValidationError(
                "Payment amount must be greater than zero."
            )

        if len(self.currency) != 3:
            raise ValidationError(
                "Currency must be a 3-character code."
            )

        if not self.provider.strip():
            raise ValidationError("Payment provider is required.")

        if self.version < 1:
            raise ValidationError("Payment version must be positive.")

    def touch(self) -> None:
        self.updated_at = utc_now()
        self.version += 1


@dataclass(slots=True)
class PaymentTransaction:
    id: UUID = field(default_factory=new_id)
    payment_id: UUID | None = None
    transaction_type: TransactionType = TransactionType.AUTHORIZATION
    amount: Decimal = Decimal("0")
    currency: str = "INR"
    status: TransactionStatus = TransactionStatus.PENDING
    provider_transaction_id: str | None = None
    error_code: str | None = None
    error_message: str | None = None
    metadata: dict[str, str] = field(default_factory=dict)
    created_at: datetime = field(default_factory=utc_now)

    def validate(self) -> None:
        if self.payment_id is None:
            raise ValidationError(
                "Transaction requires payment ID."
            )

        if self.amount <= Decimal("0"):
            raise ValidationError(
                "Transaction amount must be positive."
            )

        if len(self.currency) != 3:
            raise ValidationError(
                "Currency must be 3 characters."
            )
