from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID

from app.core.contracts import Entity
from app.core.errors import ValidationError
from app.core.ids import new_id

from .enums import (
    AvailabilityStatus,
    InventoryStatus,
    StockAdjustmentType,
    StockLocationType,
)


def utc_now() -> datetime:
    return datetime.now(UTC)


@dataclass(slots=True)
class StockLocation(Entity):

    id: UUID = field(default_factory=new_id)

    seller_id: UUID | None = None

    name: str = ""

    code: str = ""

    location_type: StockLocationType = (
        StockLocationType.WAREHOUSE
    )

    region: str | None = None

    metadata: dict[str, str] = field(
        default_factory=dict
    )

    created_at: datetime = field(
        default_factory=utc_now
    )

    updated_at: datetime = field(
        default_factory=utc_now
    )

    version: int = 1

    def validate(self) -> None:

        if not self.name.strip():
            raise ValidationError(
                "Stock location name cannot be empty."
            )

        if not self.code.strip():
            raise ValidationError(
                "Stock location code cannot be empty."
            )

        if len(self.name) > 200:
            raise ValidationError(
                "Stock location name cannot exceed 200 characters."
            )

        if len(self.code) > 100:
            raise ValidationError(
                "Stock location code cannot exceed 100 characters."
            )

        if self.version < 1:
            raise ValidationError(
                "Stock location version must be positive."
            )

    def touch(self) -> None:

        self.updated_at = utc_now()
        self.version += 1


@dataclass(slots=True)
class InventoryItem(Entity):

    id: UUID = field(default_factory=new_id)

    variant_id: UUID | None = None

    seller_id: UUID | None = None

    location_id: UUID | None = None

    status: InventoryStatus = (
        InventoryStatus.DRAFT
    )

    on_hand: int = 0

    reserved: int = 0

    incoming: int = 0

    low_stock_threshold: int = 5

    created_at: datetime = field(
        default_factory=utc_now
    )

    updated_at: datetime = field(
        default_factory=utc_now
    )

    version: int = 1

    metadata: dict[str, str] = field(
        default_factory=dict
    )

    def validate(self) -> None:

        if self.variant_id is None:
            raise ValidationError(
                "Inventory requires a variant ID."
            )

        if self.location_id is None:
            raise ValidationError(
                "Inventory requires a location ID."
            )

        if self.on_hand < 0:
            raise ValidationError(
                "On-hand inventory cannot be negative."
            )

        if self.reserved < 0:
            raise ValidationError(
                "Reserved inventory cannot be negative."
            )

        if self.incoming < 0:
            raise ValidationError(
                "Incoming inventory cannot be negative."
            )

        if self.reserved > self.on_hand:
            raise ValidationError(
                "Reserved inventory cannot exceed on-hand inventory."
            )

        if self.low_stock_threshold < 0:
            raise ValidationError(
                "Low-stock threshold cannot be negative."
            )

        if self.version < 1:
            raise ValidationError(
                "Inventory version must be positive."
            )

    @property
    def available(self) -> int:
        return self.on_hand - self.reserved

    @property
    def availability(
        self,
    ) -> AvailabilityStatus:

        if self.status != InventoryStatus.ACTIVE:
            return AvailabilityStatus.UNAVAILABLE

        if self.available <= 0:
            return AvailabilityStatus.OUT_OF_STOCK

        if self.available <= self.low_stock_threshold:
            return AvailabilityStatus.LOW_STOCK

        return AvailabilityStatus.AVAILABLE

    def touch(self) -> None:

        self.updated_at = utc_now()
        self.version += 1


@dataclass(frozen=True, slots=True)
class StockMovement:

    id: UUID = field(
        default_factory=new_id
    )

    inventory_id: UUID = field(
        default_factory=new_id
    )

    adjustment_type: StockAdjustmentType = (
        StockAdjustmentType.CORRECTION
    )

    quantity: int = 0

    reason: str = ""

    reference_id: UUID | None = None

    occurred_at: datetime = field(
        default_factory=utc_now
    )

    metadata: dict[str, str] = field(
        default_factory=dict
    )
