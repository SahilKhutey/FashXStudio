"""Pydantic schemas for Phase 08.1 Product Size Data and Phase 07.8 compatibility."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .enums import (
    AvailabilityStatus,
    MappingStatus,
    MeasurementBasis,
    MeasurementUnit,
    SizeChartStatus,
)
from .units import normalize_to_cm


class SourceProvenance(BaseModel):
    """Source provenance and audit metadata for merchant size data."""

    model_config = ConfigDict(extra="allow")

    source_id: str = Field(..., description="Authorized merchant source identifier")
    source_type: str = Field(default="API", description="API, FEED_URL, PARTNER_EXPORT, MANUAL")
    source_revision: str | None = Field(default=None, description="Source feed revision or batch hash")
    source_url: str | None = Field(default=None)
    retrieved_at: datetime | None = Field(default=None)
    verified_at: datetime | None = Field(default=None)
    metadata: dict[str, Any] | None = Field(default=None)


class SizeSystemRef(BaseModel):
    """Reference to the size system classification."""

    model_config = ConfigDict(extra="allow")

    code: str
    system_type: str = "REGIONAL_STANDARD"
    type: str | None = None
    display_name: str | None = None
    mapping_status: MappingStatus = MappingStatus.NATIVE

    def model_post_init(self, __context: Any) -> None:
        if self.display_name is None:
            self.display_name = self.code


class SizeMeasurement(BaseModel):
    """An individual linear measurement value with original and normalized units."""

    model_config = ConfigDict(extra="allow")

    field: str | None = None
    field_code: str | None = None
    attribute: str | None = None
    original_value: Decimal | None = None
    value: Decimal | None = None
    original_unit: MeasurementUnit = Field(default=MeasurementUnit.CM)
    unit: MeasurementUnit | None = None
    normalized_value: Decimal | None = Field(default=None, description="Normalized value in CM")
    normalized_unit: MeasurementUnit = Field(default=MeasurementUnit.CM)

    def model_post_init(self, __context: Any) -> None:
        # Resolve field name
        code = (self.field_code or self.field or self.attribute or "").upper()
        if not code:
            raise ValueError("Field code is required for measurement")
        self.field = code
        self.field_code = code
        self.attribute = code

        # Resolve value
        raw_val = self.original_value if self.original_value is not None else self.value
        if raw_val is None:
            raise ValueError("Measurement value is required")
        dec = Decimal(str(raw_val))
        if not dec.is_finite() or dec <= 0:
            raise ValueError(f"Measurement value must be positive and finite: {raw_val}")
        self.original_value = dec
        self.value = dec

        # Resolve unit
        eff_unit = self.unit or self.original_unit or MeasurementUnit.CM
        self.original_unit = eff_unit
        self.unit = eff_unit

        if self.normalized_value is None:
            self.normalized_value = normalize_to_cm(self.original_value, self.original_unit)


class SizeChartRow(BaseModel):
    """A row in a merchant's size chart corresponding to one merchant size label."""

    model_config = ConfigDict(extra="allow")

    merchant_size: str = Field(..., description="Original merchant size label: S, M, 38, etc.")
    sort_order: int = 0
    measurements: list[SizeMeasurement] = Field(default_factory=list)

    # Direct field shortcuts for Phase 07.8 compatibility
    chest: Decimal | None = Field(default=None, gt=0)
    waist: Decimal | None = Field(default=None, gt=0)
    hip: Decimal | None = Field(default=None, gt=0)
    length: Decimal | None = Field(default=None, gt=0)
    shoulder: Decimal | None = Field(default=None, gt=0)
    inseam: Decimal | None = Field(default=None, gt=0)
    additional_measurements: list[Any] = Field(default_factory=list)

    @field_validator("merchant_size")
    @classmethod
    def validate_size_label(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("Size label cannot be empty")
        return s

    @model_validator(mode="after")
    def validate_unique_measurement_fields(self) -> SizeChartRow:
        seen: set[str] = set()
        for m in self.measurements:
            f_code = (m.field_code or m.field or m.attribute or "").upper()
            if f_code in seen:
                raise ValueError(f"Duplicate measurement field '{f_code}' in row '{self.merchant_size}'")
            seen.add(f_code)
        return self


class SizeChartRevisionCreate(BaseModel):
    """Payload to ingest a new merchant size chart revision."""

    model_config = ConfigDict(extra="allow")

    schema_version: str = "1.0"
    merchant_product_id: str | None = None
    chart_status: SizeChartStatus = SizeChartStatus.AVAILABLE
    size_system: SizeSystemRef | None = None
    size_system_code: str | None = None
    measurement_basis: MeasurementBasis
    default_unit: MeasurementUnit = MeasurementUnit.CM
    source: SourceProvenance | None = None
    rows: list[SizeChartRow] = Field(default_factory=list)

    def model_post_init(self, __context: Any) -> None:
        if self.size_system is None:
            code = self.size_system_code or "INTL_ALPHA"
            self.size_system = SizeSystemRef(code=code)
        elif self.size_system_code is None:
            self.size_system_code = self.size_system.code

    @field_validator("rows")
    @classmethod
    def validate_unique_size_labels(cls, rows: list[SizeChartRow]) -> list[SizeChartRow]:
        if not rows:
            raise ValueError("Chart must contain at least one size row")
        seen: set[str] = set()
        for r in rows:
            norm_label = r.merchant_size.strip().upper()
            if norm_label in seen:
                raise ValueError(f"Duplicate size labels in chart: '{r.merchant_size}'")
            seen.add(norm_label)
        return rows


class SizeMeasurementResponse(BaseModel):
    """Measurement value formatted for consumer response."""

    model_config = ConfigDict(extra="allow")

    field_code: str
    display_name: str
    value: Decimal
    unit: MeasurementUnit
    normalized_cm: Decimal


class SizeChartRowResponse(BaseModel):
    """Size chart row formatted for consumer response."""

    model_config = ConfigDict(extra="allow")

    merchant_size: str
    mapped_size: str | None = None
    sort_order: int = 0
    measurements: list[SizeMeasurementResponse] = Field(default_factory=list)


class SizeChartRevisionSummary(BaseModel):
    """Summary of a historical size chart revision."""

    model_config = ConfigDict(extra="allow")

    version: int
    content_fingerprint: str
    is_current: bool = False
    size_system_code: str
    measurement_basis: MeasurementBasis
    default_unit: MeasurementUnit
    created_at: datetime
    source_id: str | None = None
    source_revision: str | None = None


class ProductSizeChartResponse(BaseModel):
    """Public shopper-facing size chart response."""

    model_config = ConfigDict(extra="allow")

    chart_id: UUID | str
    merchant_product_id: UUID | str
    merchant_id: UUID | str
    version: int = 1
    content_fingerprint: str = ""
    size_system: SizeSystemRef
    measurement_basis: MeasurementBasis
    display_unit: MeasurementUnit = MeasurementUnit.CM
    status: SizeChartStatus = SizeChartStatus.AVAILABLE
    is_stale: bool = False
    provenance: SourceProvenance
    rows: list[SizeChartRowResponse] = Field(default_factory=list)
    last_verified_at: datetime | None = None
    disclaimer: str = (
        "Size charts are supplied directly by the merchant. "
        "Virtual try-on does not verify physical garment fit or dimensions."
    )


class SizeChartUnavailableResponse(BaseModel):
    """Deterministic response when no verified chart is available."""

    model_config = ConfigDict(extra="forbid")

    product_id: str
    status: str = "UNAVAILABLE"
    message: str = "The merchant has not provided a verified size chart for this product."
    disclaimer: str = (
        "Virtual try-on does not verify physical garment fit or dimensions."
    )


class VariantStockItem(BaseModel):
    """Current availability observation for an individual variant."""

    model_config = ConfigDict(extra="allow")

    variant_id: str
    size_label: str
    colour_label: str | None = None
    sku: str | None = None
    status: AvailabilityStatus = AvailabilityStatus.UNKNOWN
    is_stale: bool = False
    observed_at: datetime | None = None


class ProductVariantAvailability(BaseModel):
    """Aggregate product availability across all merchant variants."""

    model_config = ConfigDict(extra="allow")

    merchant_product_id: UUID | str
    overall_status: AvailabilityStatus = AvailabilityStatus.UNKNOWN
    variants: list[VariantStockItem] = Field(default_factory=list)
    last_checked_at: datetime | None = None


ProductAvailabilityResponse = ProductVariantAvailability


# Backward Compatibility with Phase 07.8
class MerchantSizeChartResponse(BaseModel):
    """Verified product size chart representation for Phase 07.8 compatibility."""

    model_config = ConfigDict(extra="forbid")

    chart_id: str
    merchant_id: str
    merchant_name: str
    merchant_product_id: str
    canonical_garment_id: str | None = None
    basis: MeasurementBasis
    unit: MeasurementUnit
    status: SizeChartStatus = SizeChartStatus.VERIFIED
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
