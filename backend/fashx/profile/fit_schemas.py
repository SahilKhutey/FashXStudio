"""Pydantic v2 contracts for Phase 08.2 Shopper Fit Profile."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .units import ProfileUnit
from .validation import MeasurementValidationStatus, validate_decimal_precision


class MeasurementSubject(str, Enum):
    """Phase 08.2 invariant: Shopper profile measurements always describe BODY."""

    BODY = "BODY"


class MeasurementSource(str, Enum):
    MANUAL = "MANUAL"
    IMPORTED = "IMPORTED"


class MeasurementMethod(str, Enum):
    SELF_MEASURED = "SELF_MEASURED"
    ASSISTED_MEASUREMENT = "ASSISTED_MEASUREMENT"
    OTHER = "OTHER"


class MeasurementStatus(str, Enum):
    NOT_PROVIDED = "NOT_PROVIDED"
    PROVIDED = "PROVIDED"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    EXPIRED = "EXPIRED"
    WITHDRAWN = "WITHDRAWN"


class FitPreference(str, Enum):
    SLIM = "SLIM"
    REGULAR = "REGULAR"
    RELAXED = "RELAXED"
    OVERSIZED = "OVERSIZED"
    NO_PREFERENCE = "NO_PREFERENCE"


class ConsentPurpose(str, Enum):
    FIT_PROFILE_STORAGE = "fit_profile_storage"
    FIT_RECOMMENDATION_PROCESSING = "fit_recommendation_processing"
    THIRD_PARTY_FIT_PROCESSING = "third_party_fit_processing"
    MODEL_TRAINING = "model_training"


class MeasurementInput(BaseModel):
    """Single shopper-entered body measurement."""

    model_config = ConfigDict(extra="forbid")

    field: str = Field(..., min_length=1, max_length=32)
    value: Decimal = Field(..., gt=0)
    unit: ProfileUnit
    measured_at: datetime | None = None
    measurement_method: MeasurementMethod = MeasurementMethod.SELF_MEASURED
    confirm_unusual: bool = False

    @field_validator("field")
    @classmethod
    def normalize_field(cls, v: str) -> str:
        norm = v.strip().upper()
        if not norm:
            raise ValueError("Measurement field cannot be empty")
        return norm

    @field_validator("value")
    @classmethod
    def validate_value_precision(cls, v: Decimal) -> Decimal:
        if not v.is_finite() or v <= 0:
            raise ValueError("Measurement value must be strictly positive and finite")
        validate_decimal_precision(v, max_decimals=3)
        return v

    @field_validator("measured_at")
    @classmethod
    def normalize_measured_at_utc(cls, v: datetime | None) -> datetime | None:
        if v is None:
            return None
        if v.tzinfo is None:
            return v.replace(tzinfo=UTC)
        return v.astimezone(UTC)


class MeasurementBatchRequest(BaseModel):
    """Atomic batch of shopper body measurements (no client shopper_id accepted)."""

    model_config = ConfigDict(extra="forbid")

    measurements: list[MeasurementInput] = Field(..., min_length=1, max_length=25)

    @model_validator(mode="after")
    def validate_unique_fields(self) -> MeasurementBatchRequest:
        seen: set[str] = set()
        for item in self.measurements:
            if item.field in seen:
                raise ValueError(f"Duplicate measurement field '{item.field}' in batch")
            seen.add(item.field)
        return self


class MeasurementUpdateRequest(BaseModel):
    """Optimistically locked update to a single existing measurement."""

    model_config = ConfigDict(extra="forbid")

    value: Decimal = Field(..., gt=0)
    unit: ProfileUnit
    measured_at: datetime | None = None
    measurement_method: MeasurementMethod = MeasurementMethod.SELF_MEASURED
    confirm_unusual: bool = False
    expected_version: int = Field(..., ge=1)

    @field_validator("value")
    @classmethod
    def validate_value_precision(cls, v: Decimal) -> Decimal:
        if not v.is_finite() or v <= 0:
            raise ValueError("Measurement value must be strictly positive and finite")
        validate_decimal_precision(v, max_decimals=3)
        return v

    @field_validator("measured_at")
    @classmethod
    def normalize_measured_at_utc(cls, v: datetime | None) -> datetime | None:
        if v is None:
            return None
        if v.tzinfo is None:
            return v.replace(tzinfo=UTC)
        return v.astimezone(UTC)


class ShopperMeasurementResponse(BaseModel):
    """Shopper measurement representation retaining original and normalized units plus timestamps."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID | str
    field: str
    measurement_subject: MeasurementSubject = MeasurementSubject.BODY
    value: Decimal
    unit: ProfileUnit
    normalized_value: Decimal
    normalized_unit: ProfileUnit
    source: MeasurementSource = MeasurementSource.MANUAL
    measurement_method: MeasurementMethod = MeasurementMethod.SELF_MEASURED
    status: MeasurementStatus = MeasurementStatus.PROVIDED
    validation_status: MeasurementValidationStatus = MeasurementValidationStatus.ACCEPTED
    validation_message: str | None = None
    policy_version: str = "1.0"
    schema_version: str = "1.0"
    measured_at: datetime
    created_at: datetime
    updated_at: datetime
    verified_at: datetime | None = None
    expires_at: datetime | None = None
    needs_confirmation: bool = False
    version: int = 1


class MeasurementHistoryItem(BaseModel):
    """Audit trail entry for a change to a measurement field."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID | str
    measurement_id: UUID | str | None = None
    field: str
    previous_value: Decimal | None = None
    previous_unit: ProfileUnit | None = None
    new_value: Decimal | None = None
    new_unit: ProfileUnit | None = None
    normalized_value: Decimal | None = None
    change_source: str
    changed_at: datetime


class CategoryFitPreferenceItem(BaseModel):
    """Subjective fit preference for a garment category."""

    model_config = ConfigDict(extra="forbid")

    category: str
    fit_preference: FitPreference
    updated_at: datetime | None = None


class CategoryReadinessItem(BaseModel):
    """Per-category policy readiness summary without blocking product browsing."""

    category: str
    status: str
    policy_version: str | None = None
    required_fields: list[str] = Field(default_factory=list)
    optional_fields: list[str] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)
    message: str


class FitProfileResponse(BaseModel):
    """Shopper-controlled fit profile response."""

    status: str  # PROFILE_READY | PROFILE_INCOMPLETE
    profile_id: str
    schema_version: str = "1.0"
    preferred_unit: ProfileUnit = ProfileUnit.CM
    default_fit_preference: FitPreference = FitPreference.NO_PREFERENCE
    preference_updated_at: datetime | None = None
    measurements: list[ShopperMeasurementResponse] = Field(default_factory=list)
    category_preferences: list[CategoryFitPreferenceItem] = Field(default_factory=list)
    category_readiness: dict[str, CategoryReadinessItem] = Field(default_factory=dict)
    consents: dict[str, bool] = Field(default_factory=dict)
    version: int = 1


class PreferenceUpdateRequest(BaseModel):
    """Update subjective default fit preference and/or preferred display unit."""

    model_config = ConfigDict(extra="forbid")

    default_fit_preference: FitPreference
    preferred_unit: ProfileUnit | None = None


class CategoryPreferenceUpdateRequest(BaseModel):
    """Set subjective fit preference for a single garment category."""

    model_config = ConfigDict(extra="forbid")

    fit_preference: FitPreference


class FitConsentUpdateRequest(BaseModel):
    """Grant or withdraw purpose-specific fit profile consent."""

    model_config = ConfigDict(extra="forbid")

    granted: bool
    is_18_or_older: bool | None = None
    consent_version: str | None = None


class FitConsentStatusResponse(BaseModel):
    """Purpose-specific consent statuses for fit profile data."""

    fit_profile_storage: bool = False
    fit_recommendation_processing: bool = False
    third_party_fit_processing: bool = False
    model_training: bool = False


class MeasurementDefinitionResponse(BaseModel):
    """Public guidance metadata explaining how to measure a body field."""

    code: str
    display_name: str
    explanation: str
    tape_positioning: str
    how_to_hold: str
    example_input: str
    measurement_type: str
    supported_categories: list[str]
    default_unit: str
    is_optional_contextual: bool = False
