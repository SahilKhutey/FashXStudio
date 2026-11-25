from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class MeasurementBasis(str, Enum):
    """Whether measurements describe the human body or the finished garment."""

    BODY = "BODY"
    GARMENT = "GARMENT"


class MeasurementUnit(str, Enum):
    """Supported physical measurement units."""

    CM = "CM"
    INCH = "INCH"


class SizeChartStatus(str, Enum):
    """Lifecycle and verification status of a merchant size chart."""

    VERIFIED = "VERIFIED"
    UNVERIFIED = "UNVERIFIED"
    STALE = "STALE"
    WITHDRAWN = "WITHDRAWN"


class SizeMeasurement(BaseModel):
    """An individual measurement attribute (e.g. chest, length, waist)."""

    model_config = ConfigDict(extra="forbid")

    attribute: str = Field(..., description="Measurement attribute: chest, waist, hip, length, shoulder, etc.")
    value: Decimal = Field(..., gt=0, description="Measurement numeric value in specified unit")
    unit: MeasurementUnit = Field(default=MeasurementUnit.CM)


class SizeChartRow(BaseModel):
    """A row in a merchant's size chart for a specific size label."""

    model_config = ConfigDict(extra="forbid")

    merchant_size: str = Field(..., description="Size label as defined by merchant: S, M, L, 38, 40, etc.")
    chest: Decimal | None = Field(default=None, gt=0)
    waist: Decimal | None = Field(default=None, gt=0)
    hip: Decimal | None = Field(default=None, gt=0)
    length: Decimal | None = Field(default=None, gt=0)
    shoulder: Decimal | None = Field(default=None, gt=0)
    inseam: Decimal | None = Field(default=None, gt=0)
    additional_measurements: list[SizeMeasurement] = Field(default_factory=list)


class MerchantSizeChartResponse(BaseModel):
    """Verified product size chart representation."""

    model_config = ConfigDict(extra="forbid")

    chart_id: str
    merchant_id: str
    merchant_name: str
    merchant_product_id: str
    canonical_garment_id: str | None = None
    basis: MeasurementBasis
    unit: MeasurementUnit
    status: SizeChartStatus
    is_stale: bool = False
    source_reference: str = Field(..., description="Internal merchant provenance identifier")
    source_revision: str
    chart_version: int = 1
    last_verified_at: datetime | None = None
    rows: list[SizeChartRow] = Field(default_factory=list)
    disclaimer: str = (
        "Size charts are supplied directly by the merchant. "
        "Virtual try-on does not verify physical garment fit or dimensions."
    )


class SizeChartUnavailableResponse(BaseModel):
    """Response returned when no verified merchant size chart exists."""

    model_config = ConfigDict(extra="forbid")

    product_id: str
    status: str = "UNAVAILABLE"
    message: str = "The merchant has not provided a verified size chart for this product."
    disclaimer: str = "Virtual try-on does not verify physical garment fit or dimensions."
