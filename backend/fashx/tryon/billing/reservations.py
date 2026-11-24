"""Atomic budget reservation models and status definitions."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Any
from uuid import UUID


class BudgetScope(str, Enum):
    PLATFORM = "PLATFORM"
    MERCHANT = "MERCHANT"
    USER = "USER"


class BudgetPeriod(str, Enum):
    DAILY = "DAILY"
    MONTHLY = "MONTHLY"


class BudgetStatus(str, Enum):
    ACTIVE = "ACTIVE"
    EXCEEDED = "EXCEEDED"
    SUSPENDED = "SUSPENDED"


class ReservationStatus(str, Enum):
    RESERVED = "RESERVED"
    COMMITTED = "COMMITTED"
    RELEASED = "RELEASED"
    TIMED_OUT = "TIMED_OUT"
    HELD_FOR_RECONCILIATION = "HELD_FOR_RECONCILIATION"


class BudgetExceededError(Exception):
    """Raised when an operation would exceed platform, merchant, or user budget ceilings."""

    def __init__(
        self,
        message: str,
        scope_type: str,
        scope_id: str,
        hard_limit: Decimal,
        current_spend: Decimal,
        reserved_spend: Decimal,
        requested_amount: Decimal,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.scope_type = scope_type
        self.scope_id = scope_id
        self.hard_limit = hard_limit
        self.current_spend = current_spend
        self.reserved_spend = reserved_spend
        self.requested_amount = requested_amount

    def as_json(self) -> dict[str, Any]:
        return {
            "error": "budget_exceeded",
            "message": self.message,
            "scope_type": self.scope_type,
            "scope_id": self.scope_id,
            "hard_limit": str(self.hard_limit),
            "current_spend": str(self.current_spend),
            "reserved_spend": str(self.reserved_spend),
            "requested_amount": str(self.requested_amount),
        }


@dataclass
class ReservationResult:
    """Outcome of an atomic budget reservation."""

    success: bool
    reservation_id: UUID | None
    budget_id: UUID | None
    reserved_amount: Decimal
    error_message: str | None = None
