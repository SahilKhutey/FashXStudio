from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from app.core.errors import ValidationError
from app.core.ids import new_id

from .enums import (
    CancellationStatus,
    RefundReason,
    RefundStatus,
    ReplacementStatus,
    ReturnReason,
    ReturnStatus,
)


def utc_now() -> datetime:
    return datetime.now(UTC)


@dataclass(slots=True)
class ReturnRequest:
    id: UUID = field(default_factory=new_id)
    order_id: UUID | None = None
    customer_id: UUID | None = None
    status: ReturnStatus = ReturnStatus.REQUESTED
    reason: ReturnReason = ReturnReason.OTHER
    notes: str = ""
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)
    version: int = 1
    metadata: dict[str, str] = field(default_factory=dict)

    def validate(self) -> None:
        if self.order_id is None:
            raise ValidationError("Return requires order ID.")

        if self.customer_id is None:
            raise ValidationError("Return requires customer ID.")

        if self.version < 1:
            raise ValidationError("Return version must be positive.")

    def touch(self) -> None:
        self.updated_at = utc_now()
        self.version += 1


@dataclass(slots=True)
class ReturnLine:
    id: UUID = field(default_factory=new_id)
    return_id: UUID | None = None
    order_line_id: UUID | None = None
    product_id: UUID | None = None
    variant_id: UUID | None = None
    quantity: int = 1
    refund_amount: Decimal = Decimal("0.00")
    metadata: dict[str, str] = field(default_factory=dict)

    def validate(self) -> None:
        if self.return_id is None:
            raise ValidationError("Return line requires return ID.")

        if self.order_line_id is None:
            raise ValidationError("Return line requires order line ID.")

        if self.product_id is None:
            raise ValidationError("Return line requires product ID.")

        if self.quantity < 1:
            raise ValidationError("Return quantity must be at least 1.")

        if self.refund_amount < Decimal("0"):
            raise ValidationError("Refund amount cannot be negative.")


@dataclass(slots=True)
class CancellationRequest:
    id: UUID = field(default_factory=new_id)
    order_id: UUID | None = None
    customer_id: UUID | None = None
    status: CancellationStatus = CancellationStatus.REQUESTED
    reason: str = ""
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)
    version: int = 1

    def validate(self) -> None:
        if self.order_id is None:
            raise ValidationError("Cancellation requires order ID.")

        if self.customer_id is None:
            raise ValidationError("Cancellation requires customer ID.")

        if not self.reason.strip():
            raise ValidationError("Cancellation reason is required.")

    def touch(self) -> None:
        self.updated_at = utc_now()
        self.version += 1


@dataclass(slots=True)
class Refund:
    id: UUID = field(default_factory=new_id)
    order_id: UUID | None = None
    return_id: UUID | None = None
    payment_id: UUID | None = None
    amount: Decimal = Decimal("0.00")
    currency: str = "INR"
    reason: RefundReason = RefundReason.OTHER
    status: RefundStatus = RefundStatus.REQUESTED
    provider_reference: str | None = None
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)
    version: int = 1
    metadata: dict[str, str] = field(default_factory=dict)

    def validate(self) -> None:
        if self.order_id is None:
            raise ValidationError("Refund requires order ID.")

        if self.amount <= Decimal("0"):
            raise ValidationError("Refund amount must be positive.")

        if len(self.currency) != 3:
            raise ValidationError("Currency must be a 3-character code.")

    def touch(self) -> None:
        self.updated_at = utc_now()
        self.version += 1


@dataclass(slots=True)
class ReplacementRequest:
    id: UUID = field(default_factory=new_id)
    order_id: UUID | None = None
    return_id: UUID | None = None
    original_order_line_id: UUID | None = None
    replacement_product_id: UUID | None = None
    replacement_variant_id: UUID | None = None
    status: ReplacementStatus = ReplacementStatus.REQUESTED
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)
    version: int = 1

    def validate(self) -> None:
        if self.order_id is None:
            raise ValidationError("Replacement requires order ID.")

        if self.original_order_line_id is None:
            raise ValidationError("Replacement requires original order line.")

        if self.replacement_product_id is None:
            raise ValidationError("Replacement product is required.")

    def touch(self) -> None:
        self.updated_at = utc_now()
        self.version += 1
