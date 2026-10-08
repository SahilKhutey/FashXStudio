from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from fashx.core.errors import ValidationError

from .enums import Currency

_TWO_PLACES = Decimal("0.01")


@dataclass(frozen=True, slots=True)
class Money:
    amount: Decimal
    currency: Currency

    def __post_init__(self) -> None:
        if not isinstance(self.amount, Decimal):
            object.__setattr__(self, "amount", Decimal(str(self.amount)))
        object.__setattr__(
            self,
            "amount",
            self.amount.quantize(_TWO_PLACES, rounding=ROUND_HALF_UP),
        )

    def subtract(self, other: Money) -> Money:
        if self.currency != other.currency:
            raise ValidationError(
                f"Cannot subtract money of different currencies: {self.currency} and {other.currency}"
            )
        return Money(
            amount=self.amount - other.amount,
            currency=self.currency,
        )

    def add(self, other: Money) -> Money:
        if self.currency != other.currency:
            raise ValidationError(
                f"Cannot add money of different currencies: {self.currency} and {other.currency}"
            )
        return Money(
            amount=self.amount + other.amount,
            currency=self.currency,
        )


def money(amount: str | int | float | Decimal, currency: Currency) -> Money:
    return Money(
        amount=Decimal(str(amount)),
        currency=currency,
    )
