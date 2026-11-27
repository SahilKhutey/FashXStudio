"""Deterministic measurement comparison engine (Phase 08.3 - Task 8.3.1).

Strictly compares compatible decimal body measurements against merchant body-chart ranges
without pre-rounding, and never compares half-garment widths or raw garment dimensions
directly against body circumferences without an approved EaseRule.
"""

from __future__ import annotations

from dataclasses import dataclass

from fashx.fit.contracts import MeasurementValue, SizeRange
from fashx.fit.ease_policy import EaseRule, evaluate_ease
from fashx.fit.enums import MeasurementBasis

_HALF_OR_FLAT_WIDTH_MARKERS = ("HALF_", "_WIDTH", "FLAT_")


def _ensure_compatible_field(shopper_field: str, chart_field: str) -> None:
    s_field = shopper_field.strip().upper()
    c_field = chart_field.strip().upper()
    if any(marker in c_field for marker in _HALF_OR_FLAT_WIDTH_MARKERS) and not any(
        marker in s_field for marker in _HALF_OR_FLAT_WIDTH_MARKERS
    ):
        raise ValueError(
            f"Incompatible measurement definition: cannot compare body circumference '{s_field}' "
            f"against flat/half garment dimension '{c_field}'."
        )
    if s_field != c_field:
        raise ValueError(f"Measurement fields do not match: '{s_field}' vs '{c_field}'.")


def measurement_matches(
    shopper_measurement: MeasurementValue,
    size_range: SizeRange,
) -> bool:
    """Compare one shopper body measurement against a BODY-basis size chart range.

    Uses exact Decimal inclusive range bounds L_{m,s} <= B_m <= U_{m,s} with no rounding.
    Refuses mismatched field definitions, inverted ranges, and GARMENT/UNKNOWN chart bases.
    """
    _ensure_compatible_field(shopper_measurement.field, size_range.field)
    if size_range.basis != MeasurementBasis.BODY:
        raise ValueError(
            f"Direct body matcher cannot evaluate '{size_range.basis.value}' basis ranges for "
            f"field '{size_range.field}'; validated ease evidence is required."
        )
    if not size_range.valid_range():
        raise ValueError(
            f"Invalid size chart range for '{size_range.field}': "
            f"{size_range.minimum_cm} > {size_range.maximum_cm}."
        )
    value = shopper_measurement.value_cm
    return size_range.minimum_cm <= value <= size_range.maximum_cm


def evaluate_size(
    shopper_measurements: dict[str, MeasurementValue],
    size_ranges: list[SizeRange],
    required_fields: tuple[str, ...],
) -> tuple[bool, list[str]]:
    """Evaluate all required body fields for one candidate size option.

    Returns (all_required_matched, mismatched_or_missing_fields).
    """
    range_by_field: dict[str, SizeRange] = {}
    for item in size_ranges:
        if not item.valid_range():
            raise ValueError(
                f"Invalid size chart range for '{item.field}': {item.minimum_cm} > {item.maximum_cm}."
            )
        range_by_field[item.field] = item

    mismatches: list[str] = []
    for field in required_fields:
        req = field.strip().upper()
        shopper_val = shopper_measurements.get(req)
        chart_range = range_by_field.get(req)
        if shopper_val is None or chart_range is None:
            mismatches.append(req)
            continue
        if not measurement_matches(shopper_val, chart_range):
            mismatches.append(req)

    return len(mismatches) == 0, mismatches


@dataclass(frozen=True)
class CandidateEvaluationDetail:
    """Detailed comparison telemetry for a single merchant size row."""

    matched: bool
    mismatched_fields: tuple[str, ...]
    optional_matches: tuple[str, ...]
    ease_evaluated: bool


def evaluate_size_detailed(
    *,
    shopper_measurements: dict[str, MeasurementValue],
    size_ranges: list[SizeRange],
    required_fields: tuple[str, ...],
    optional_fields: tuple[str, ...] = (),
    chart_basis: MeasurementBasis = MeasurementBasis.BODY,
    ease_rules: dict[str, EaseRule] | None = None,
) -> CandidateEvaluationDetail:
    """Evaluate candidate size with explicit BODY vs GARMENT basis separation."""
    range_by_field: dict[str, SizeRange] = {}
    for item in size_ranges:
        if not item.valid_range():
            raise ValueError(
                f"Invalid size chart range for '{item.field}': {item.minimum_cm} > {item.maximum_cm}."
            )
        range_by_field[item.field] = item

    mismatches: list[str] = []
    optional_hits: list[str] = []
    ease_used = False

    if chart_basis == MeasurementBasis.BODY:
        ok, mismatches = evaluate_size(shopper_measurements, size_ranges, required_fields)
        for opt in optional_fields:
            s_val = shopper_measurements.get(opt)
            c_rng = range_by_field.get(opt)
            if (
                s_val is not None
                and c_rng is not None
                and c_rng.basis == MeasurementBasis.BODY
                and measurement_matches(s_val, c_rng)
            ):
                optional_hits.append(opt)
        return CandidateEvaluationDetail(
            matched=ok,
            mismatched_fields=tuple(mismatches),
            optional_matches=tuple(optional_hits),
            ease_evaluated=False,
        )

    if chart_basis == MeasurementBasis.GARMENT:
        if not ease_rules:
            raise ValueError(
                "GARMENT basis comparison requires approved EaseRule definitions for all required fields."
            )
        for field in required_fields:
            req = field.strip().upper()
            s_val = shopper_measurements.get(req)
            c_rng = range_by_field.get(req)
            rule = ease_rules.get(req)
            if s_val is None or c_rng is None or rule is None:
                mismatches.append(req)
                continue
            _ensure_compatible_field(s_val.field, c_rng.field)
            # Finished garment dimension must be checked via E = G - B against validated ease bounds
            # If merchant gave a garment tolerance band [min, max], both bounds must satisfy the rule
            # or use midpoint when min == max.
            low_res = evaluate_ease(body_cm=s_val.value_cm, garment_cm=c_rng.minimum_cm, rule=rule)
            high_res = evaluate_ease(body_cm=s_val.value_cm, garment_cm=c_rng.maximum_cm, rule=rule)
            ease_used = ease_used or low_res.evaluated
            if not (low_res.within_policy and high_res.within_policy):
                mismatches.append(req)

        return CandidateEvaluationDetail(
            matched=len(mismatches) == 0,
            mismatched_fields=tuple(mismatches),
            optional_matches=tuple(optional_hits),
            ease_evaluated=ease_used,
        )

    raise ValueError(f"Unsupported measurement basis '{chart_basis}'.")
