"""Unit tests for Measurement Matcher, Category Policies, and Ease Policies (FIT-831..833)."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from fashx.fit.category_policy import get_category_fit_policy
from fashx.fit.contracts import MeasurementValue, SizeRange
from fashx.fit.ease_policy import EasePolicyRegistry, EaseRule, evaluate_ease
from fashx.fit.enums import FitPreference, MeasurementBasis
from fashx.fit.measurement_matcher import evaluate_size, evaluate_size_detailed, measurement_matches


def _m(field: str, value: str) -> MeasurementValue:
    return MeasurementValue(
        field=field,
        value_cm=Decimal(value),
        measured_at=datetime.now(UTC),
        revision=1,
        provenance="SHOPPER_ENTERED",
    )


def _r(
    field: str,
    low: str,
    high: str,
    *,
    basis: MeasurementBasis = MeasurementBasis.BODY,
) -> SizeRange:
    return SizeRange(
        field=field,
        minimum_cm=Decimal(low),
        maximum_cm=Decimal(high),
        basis=basis,
    )


def test_fit_831_boundary_matching_and_rejections() -> None:
    # FIT-831-001..005: exact Decimal inclusive boundaries without rounding
    chest_range = _r("CHEST", "93", "97")
    assert measurement_matches(_m("CHEST", "96"), chest_range) is True
    assert measurement_matches(_m("CHEST", "93"), chest_range) is True
    assert measurement_matches(_m("CHEST", "97"), chest_range) is True
    assert measurement_matches(_m("CHEST", "92.999"), chest_range) is False
    assert measurement_matches(_m("CHEST", "97.001"), chest_range) is False

    # FIT-831-006: measurement field mismatch raises ValueError
    with pytest.raises(ValueError, match="do not match"):
        measurement_matches(_m("WAIST", "82"), chest_range)

    # Half/flat garment width vs circumference is blocked
    with pytest.raises(ValueError, match="Incompatible measurement definition"):
        measurement_matches(_m("CHEST", "96"), _r("HALF_CHEST_WIDTH", "48", "50"))

    # FIT-831-007: invalid inverted range raises ValueError
    with pytest.raises(ValueError, match="Invalid size chart range"):
        measurement_matches(_m("CHEST", "95"), _r("CHEST", "98", "94"))


def test_fit_831_evaluate_size_ignores_unrequired_fields() -> None:
    matched, mismatches = evaluate_size(
        {"CHEST": _m("CHEST", "96")},
        [_r("CHEST", "93", "97"), _r("WAIST", "80", "85")],
        required_fields=("CHEST",),
    )
    assert matched is True
    assert mismatches == []

    # Missing required field fails closed
    matched2, mismatches2 = evaluate_size(
        {},
        [_r("CHEST", "93", "97")],
        required_fields=("CHEST",),
    )
    assert matched2 is False
    assert mismatches2 == ["CHEST"]


def test_fit_832_category_fit_policies() -> None:
    # FIT-832-001: TSHIRTS enabled with BODY basis and CHEST requirement
    tshirt = get_category_fit_policy("t-shirts")
    assert tshirt is not None
    assert tshirt.enabled is True
    assert tshirt.required_measurements == ("CHEST",)
    assert tshirt.supported_bases == (MeasurementBasis.BODY,)

    # FIT-832-002: TROUSERS intentionally disabled until validated
    trousers = get_category_fit_policy("trousers")
    assert trousers is not None
    assert trousers.enabled is False

    # Sarees unsupported / disabled
    sarees = get_category_fit_policy("sarees")
    assert sarees is not None
    assert sarees.enabled is False

    # FIT-832-003: Unknown category returns None
    assert get_category_fit_policy("spacesuits") is None


def test_fit_833_ease_separation_and_validated_rules() -> None:
    # Body matcher rejects GARMENT basis ranges directly
    with pytest.raises(ValueError, match="Direct body matcher cannot evaluate 'GARMENT'"):
        measurement_matches(
            _m("CHEST", "96"),
            _r("CHEST", "106", "106", basis=MeasurementBasis.GARMENT),
        )

    # Missing EaseRule cannot guess suitability (FIT-833-002)
    missing_ease = evaluate_ease(body_cm=Decimal("96"), garment_cm=Decimal("106"), rule=None)
    assert missing_ease.evaluated is False
    assert missing_ease.within_policy is False
    assert missing_ease.calculated_ease_cm == Decimal("10")
    assert missing_ease.reason == "FIT_POLICY_MISSING"

    # Validated EaseRule evaluates garment range cleanly (FIT-833-003)
    rule = EaseRule(
        category="TSHIRTS",
        measurement="CHEST",
        basis=MeasurementBasis.GARMENT,
        intended_fit=FitPreference.RELAXED,
        garment_construction="COTTON_JERSEY_CREW",
        minimum_cm=Decimal("8"),
        maximum_cm=Decimal("12"),
        policy_version="ease-v1",
        evidence_reference="specialist-review-2026-01",
    )
    reg = EasePolicyRegistry(approved_rules=[rule])
    fetched = reg.get_rule(
        category="TSHIRTS",
        measurement="CHEST",
        basis=MeasurementBasis.GARMENT,
        intended_fit=FitPreference.RELAXED,
    )
    assert fetched is not None

    detail = evaluate_size_detailed(
        shopper_measurements={"CHEST": _m("CHEST", "96")},
        size_ranges=[_r("CHEST", "106", "106", basis=MeasurementBasis.GARMENT)],
        required_fields=("CHEST",),
        chart_basis=MeasurementBasis.GARMENT,
        ease_rules={"CHEST": fetched},
    )
    assert detail.matched is True
    assert detail.ease_evaluated is True
