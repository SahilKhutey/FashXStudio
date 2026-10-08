from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field

from fashx.domain.inventory.enums import (
    AvailabilityStatus,
    InventoryStatus,
    StockAdjustmentType,
    StockLocationType,
)


class StockLocationCreateRequest(BaseModel):
    seller_id: UUID | None = None
    name: str = Field(
        min_length=1,
        max_length=200,
    )
    code: str = Field(
        min_length=1,
        max_length=100,
    )
    location_type: StockLocationType = StockLocationType.WAREHOUSE
    region: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)


class StockLocationResponse(BaseModel):
    id: UUID
    seller_id: UUID | None
    name: str
    code: str
    location_type: StockLocationType
    region: str | None
    version: int


class InventoryCreateRequest(BaseModel):
    variant_id: UUID
    seller_id: UUID | None = None
    location_id: UUID
    on_hand: int = Field(
        default=0,
        ge=0,
    )
    incoming: int = Field(
        default=0,
        ge=0,
    )
    low_stock_threshold: int = Field(
        default=5,
        ge=0,
    )
    metadata: dict[str, str] = Field(default_factory=dict)


class InventoryStatusRequest(BaseModel):
    status: InventoryStatus


class StockAdjustmentRequest(BaseModel):
    adjustment_type: StockAdjustmentType
    quantity: int = Field(gt=0)
    reason: str = ""


class InventoryResponse(BaseModel):
    id: UUID
    variant_id: UUID
    seller_id: UUID | None
    location_id: UUID
    status: InventoryStatus
    on_hand: int
    reserved: int
    incoming: int
    available: int
    availability: AvailabilityStatus
    low_stock_threshold: int
    version: int
