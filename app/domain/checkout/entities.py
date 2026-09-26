from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID

from app.core.errors import ValidationError
from app.core.ids import new_id

from .enums import CheckoutStatus


def utc_now() -> datetime:
    return datetime.now(UTC)


@dataclass(slots=True)
class CheckoutSession:
    id: UUID = field(default_factory=new_id)
    cart_id: UUID | None = None
    customer_id: UUID | None = None
    status: CheckoutStatus = CheckoutStatus.OPEN
    currency: str = "INR"
    shipping_address_id: UUID | None = None
    billing_address_id: UUID | None = None
    order_id: UUID | None = None
    expires_at: datetime | None = None
    metadata: dict[str, str] = field(default_factory=dict)
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)
    version: int = 1
    # Backward compatibility fields
    email: str | None = None
    idempotency_key: str | None = None

    def validate(self) -> None:
        if self.cart_id is None:
            raise ValidationError("Checkout requires cart_id.")

        if len(self.currency) != 3:
            raise ValidationError("Currency must be 3 characters.")

        if self.version < 1:
            raise ValidationError("Version must be positive.")

    def is_expired(
        self,
        timestamp: datetime | None = None,
    ) -> bool:
        if self.expires_at is None:
            return False

        timestamp = timestamp or utc_now()
        return timestamp >= self.expires_at

    def touch(self) -> None:
        self.updated_at = utc_now()
        self.version += 1
