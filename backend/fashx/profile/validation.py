"""Measurement range, decimal precision, and freshness validation (Phase 08.2 - Task 8.2.5 & 8.2.6)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from enum import Enum

from .measurement_definitions import MEASUREMENT_DEFINITIONS
from .units import ProfileUnit, normalize_measurement_value

VALIDATION_POLICY_VERSION = "1.0"
DEFAULT_MEASUREMENT_STALE_DAYS = 180


class MeasurementValidationStatus(str, Enum):
    """Explicit outcome states for body measurement range and plausibility checks."""

    ACCEPTED = "ACCEPTED"
    WARNING = "WARNING"
    NEEDS_CONFIRMATION = "NEEDS_CONFIRMATION"
    REJECTED = "REJECTED"


@dataclass(frozen=True)
class MeasurementRange:
    """Provisional plausibility bounds in normalized canonical unit (CM or KG)."""

    minimum: Decimal
    maximum: Decimal
    hard_minimum: Decimal
    hard_maximum: Decimal


# Provisional bounds (versioned). Out-of-provisional-bounds within hard technical limits trigger
# NEEDS_CONFIRMATION so shoppers with valid unusual measurements can confirm rather than be locked out.
RANGES: dict[str, MeasurementRange] = {
    code: MeasurementRange(
        minimum=Decimal(defn.minimum_cm),
        maximum=Decimal(defn.maximum_cm),
        hard_minimum=Decimal("1.00"),
        hard_maximum=Decimal("500.00"),
    )
    for code, defn in MEASUREMENT_DEFINITIONS.items()
}


@dataclass(frozen=True)
class MeasurementValidationOutcome:
    """Result of validating and normalizing an incoming measurement."""

    field: str
    normalized_value: Decimal
    normalized_unit: ProfileUnit
    validation_status: MeasurementValidationStatus
    policy_version: str
    message: str | None = None


def validate_decimal_precision(value: Decimal, max_decimals: int = 3) -> None:
    """Reject values with more than `max_decimals` fractional digits."""
    exp = value.as_tuple().exponent
    if isinstance(exp, int) and exp < -max_decimals:
        raise ValueError(f"Use up to {max_decimals} decimal places.")


def validate_measurement(
    field: str,
    value: Decimal,
    unit: ProfileUnit | str,
    *,
    confirm_unusual: bool = False,
) -> MeasurementValidationOutcome:
    """Normalize and evaluate a body measurement against hard bounds and provisional plausibility bounds."""
    norm_field = field.strip().upper()
    if norm_field not in MEASUREMENT_DEFINITIONS or norm_field not in RANGES:
        raise ValueError(f"Unknown measurement field '{field}'.")

    if not value.is_finite() or value <= 0:
        raise ValueError("Measurement value must be strictly positive and finite.")

    validate_decimal_precision(value, max_decimals=3)

    normalized_val, normalized_unit = normalize_measurement_value(norm_field, value, unit)
    bounds = RANGES[norm_field]

    if normalized_val < bounds.hard_minimum or normalized_val > bounds.hard_maximum:
        raise ValueError(
            f"{norm_field} value {normalized_val} {normalized_unit.value} is outside technical bounds "
            f"[{bounds.hard_minimum}, {bounds.hard_maximum}]."
        )

    if normalized_val < bounds.minimum or normalized_val > bounds.maximum:
        if confirm_unusual:
            return MeasurementValidationOutcome(
                field=norm_field,
                normalized_value=normalized_val,
                normalized_unit=normalized_unit,
                validation_status=MeasurementValidationStatus.WARNING,
                policy_version=VALIDATION_POLICY_VERSION,
                message=(
                    f"Confirmed {norm_field} ({normalized_val} {normalized_unit.value}) saved under "
                    "exception policy."
                ),
            )
        return MeasurementValidationOutcome(
            field=norm_field,
            normalized_value=normalized_val,
            normalized_unit=normalized_unit,
            validation_status=MeasurementValidationStatus.NEEDS_CONFIRMATION,
            policy_version=VALIDATION_POLICY_VERSION,
            message=(
                f"Please double-check your {norm_field.lower()} entry ({normalized_val} {normalized_unit.value}). "
                f"Expected typical range is {bounds.minimum}–{bounds.maximum} {normalized_unit.value}; "
                "confirm if this value is accurate."
            ),
        )

    return MeasurementValidationOutcome(
        field=norm_field,
        normalized_value=normalized_val,
        normalized_unit=normalized_unit,
        validation_status=MeasurementValidationStatus.ACCEPTED,
        policy_version=VALIDATION_POLICY_VERSION,
        message=None,
    )


def evaluate_measurement_freshness(
    measured_at: datetime | None,
    updated_at: datetime | None = None,
    *,
    max_age_days: int = DEFAULT_MEASUREMENT_STALE_DAYS,
    now: datetime | None = None,
) -> tuple[bool, str]:
    """Return (needs_confirmation, status_str) based on measurement age.

    Rule: Old measurements are never silently deleted; they transition to NEEDS_REVIEW /
    confirmation advisory after `max_age_days`.
    """
    reference_ts = measured_at or updated_at
    if reference_ts is None:
        return True, "NEEDS_REVIEW"

    if reference_ts.tzinfo is None:
        reference_ts = reference_ts.replace(tzinfo=UTC)

    current = now or datetime.now(UTC)
    if current.tzinfo is None:
        current = current.replace(tzinfo=UTC)

    if current - reference_ts > timedelta(days=max_age_days):
        return True, "NEEDS_REVIEW"

    return False, "PROVIDED"
