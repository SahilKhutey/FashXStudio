"""Internal evidence completeness scoring and hard eligibility gate (Phase 08.3 - Task 8.3.6).

IMPORTANT: The score calculated here is an INTERNAL_EVIDENCE_SCORE for evaluation and
threshold tuning. It MUST NOT be shown to shoppers as a calibrated probability unless
calibration has been empirically demonstrated on independently labelled data.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

WEIGHTS: dict[str, Decimal] = {
    "profile_quality": Decimal("0.25"),
    "chart_quality": Decimal("0.25"),
    "category_quality": Decimal("0.20"),
    "measurement_compatibility": Decimal("0.20"),
    "variant_validity": Decimal("0.10"),
}

DEFAULT_INTERNAL_THRESHOLD = Decimal("0.750")


def calculate_evidence_score(dimensions: dict[str, Decimal]) -> Decimal:
    """Compute weighted evidence score from normalized [0, 1] quality dimensions."""
    if set(dimensions.keys()) != set(WEIGHTS.keys()):
        raise ValueError(
            f"Incomplete confidence dimensions; expected {sorted(WEIGHTS.keys())}, "
            f"got {sorted(dimensions.keys())}."
        )
    for key, value in dimensions.items():
        if value < Decimal("0") or value > Decimal("1"):
            raise ValueError(f"Confidence dimension '{key}'={value} out of range [0, 1].")

    score = sum((dimensions[key] * weight for key, weight in WEIGHTS.items()), Decimal("0"))
    return score.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)


def build_evidence_dimensions(
    *,
    required_count: int,
    present_shopper_count: int,
    shopper_fresh: bool,
    chart_present: bool,
    chart_fresh: bool,
    chart_basis_known: bool,
    category_enabled: bool,
    compatible_field_count: int,
    variant_available: bool,
) -> dict[str, Decimal]:
    """Derive deterministic [0, 1] dimension scores from observed evidence state."""
    if required_count <= 0:
        profile_q = Decimal("0")
        compat_q = Decimal("0")
    else:
        ratio = Decimal(min(present_shopper_count, required_count)) / Decimal(required_count)
        profile_q = ratio if shopper_fresh else (ratio * Decimal("0.5"))
        compat_q = Decimal(min(compatible_field_count, required_count)) / Decimal(required_count)

    chart_q = Decimal("0")
    if chart_present and chart_basis_known:
        chart_q = Decimal("1.0") if chart_fresh else Decimal("0.5")
    elif chart_present:
        chart_q = Decimal("0.4")

    category_q = Decimal("1.0") if category_enabled else Decimal("0.0")
    variant_q = Decimal("1.0") if variant_available else Decimal("0.0")

    return {
        "profile_quality": min(Decimal("1"), max(Decimal("0"), profile_q)),
        "chart_quality": min(Decimal("1"), max(Decimal("0"), chart_q)),
        "category_quality": category_q,
        "measurement_compatibility": min(Decimal("1"), max(Decimal("0"), compat_q)),
        "variant_validity": variant_q,
    }


def may_recommend(
    *,
    evidence_eligible: bool,
    score: Decimal,
    internal_threshold: Decimal = DEFAULT_INTERNAL_THRESHOLD,
) -> bool:
    """Apply hard eligibility gates before checking numeric internal threshold."""
    if not evidence_eligible:
        return False
    return score >= internal_threshold
