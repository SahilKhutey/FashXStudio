"""Size chart validation and numeric range checking service for Phase 08.1."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from .enums import MeasurementBasis
from .measurement_fields import FIELD_DEFINITIONS, is_field_valid_for_category
from .schemas import SizeChartRevisionCreate
from .units import normalize_to_cm


@dataclass(frozen=True)
class ValidationIssue:
    """Represents a validation problem or review advisory on an incoming size chart."""

    code: str
    severity: str  # ERROR | WARNING | REVIEW
    message: str
    row_label: str | None = None
    field: str | None = None


@dataclass
class ValidationResult:
    """Aggregated validation result container."""

    issues: list[ValidationIssue]

    @property
    def is_valid(self) -> bool:
        return not any(i.severity == "ERROR" for i in self.issues)

    @property
    def errors(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.severity == "ERROR"]

    @property
    def warnings(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.severity == "WARNING"]

    def __iter__(self):
        return iter(self.issues)


def validate_chart(
    chart: SizeChartRevisionCreate,
    category: str = "GENERAL",
    *,
    garment_category: str | None = None,
) -> ValidationResult:
    """Validate a merchant size chart revision against schema, category, basis, and range policies."""
    issues: list[ValidationIssue] = []
    effective_cat = (garment_category or category or "GENERAL").upper()

    # 1. Basis verification
    if chart.measurement_basis == MeasurementBasis.UNKNOWN:
        issues.append(
            ValidationIssue(
                code="UNKNOWN_MEASUREMENT_BASIS",
                severity="REVIEW",
                message="Chart does not declare whether measurements describe BODY or GARMENT.",
            )
        )

    # 2. Rows & Measurements validation
    if not chart.rows:
        issues.append(
            ValidationIssue(
                code="EMPTY_CHART_ROWS",
                severity="ERROR",
                message="Chart contains no size rows.",
            )
        )
        return ValidationResult(issues=issues)

    observed_progressions: dict[str, list[tuple[str, Decimal]]] = {}

    for row in chart.rows:
        row_label = row.merchant_size

        for m in row.measurements:
            field_code = (m.field_code or m.field or "").upper()
            definition = FIELD_DEFINITIONS.get(field_code)

            if definition is None:
                issues.append(
                    ValidationIssue(
                        code="UNKNOWN_FIELD",
                        severity="ERROR",
                        message=f"Measurement field '{field_code}' is not registered in measurement registry.",
                        row_label=row_label,
                        field=field_code,
                    )
                )
                continue

            # Check category eligibility
            if not is_field_valid_for_category(field_code, effective_cat):
                issues.append(
                    ValidationIssue(
                        code="INCOMPATIBLE_FIELD_CATEGORY",
                        severity="ERROR",
                        message=(
                            f"Measurement field '{field_code}' is not permitted for category '{effective_cat}'."
                        ),
                        row_label=row_label,
                        field=field_code,
                    )
                )

            # Range validation on normalized cm value
            norm_val = normalize_to_cm(m.original_value, m.original_unit)
            if norm_val is not None:
                dec_val = Decimal(str(norm_val))
                min_dec = Decimal(str(definition.minimum_cm))
                max_dec = Decimal(str(definition.maximum_cm))

                if dec_val < min_dec or dec_val > max_dec:
                    issues.append(
                        ValidationIssue(
                            code="MEASUREMENT_OUT_OF_BOUNDS",
                            severity="ERROR",
                            message=(
                                f"Value {dec_val} cm is outside approved range "
                                f"[{definition.minimum_cm}, {definition.maximum_cm}] cm for {field_code}."
                            ),
                            row_label=row_label,
                            field=field_code,
                        )
                    )

                observed_progressions.setdefault(field_code, []).append((row_label, dec_val))

    # 3. Cross-row progression review (Advisory WARNING)
    for field_code, vals in observed_progressions.items():
        if len(vals) >= 2:
            for i in range(len(vals) - 1):
                label_a, val_a = vals[i]
                label_b, val_b = vals[i + 1]
                if val_b < val_a:
                    issues.append(
                        ValidationIssue(
                            code="UNUSUAL_PROGRESSION",
                            severity="WARNING",
                            message=(
                                f"Measurement for {field_code} in size '{label_b}' ({val_b} cm) is smaller than "
                                f"size '{label_a}' ({val_a} cm)."
                            ),
                            row_label=label_b,
                            field=field_code,
                        )
                    )

    return ValidationResult(issues=issues)


def chart_is_publishable(result_or_issues: Any) -> bool:
    """Return True if no fatal ERROR issues exist."""
    if isinstance(result_or_issues, ValidationResult):
        return result_or_issues.is_valid
    if isinstance(result_or_issues, list):
        return not any(getattr(issue, "severity", None) == "ERROR" for issue in result_or_issues)
    return True
