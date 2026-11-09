"""RC13 Product Validation and Pre-Registered Pilot Metric Evaluator.

Strictly aligned with frozen docs/pilot/pilot-plan.md (Phase 10 Closed Pilot).
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any


class ProductDecision(StrEnum):
    GO = "go"
    FIX_AND_RERUN = "fix_and_rerun"
    PIVOT_OR_STOP = "pivot_or_stop"
    HOLD = "hold"


@dataclass(frozen=True)
class ProductMetric:
    name: str
    value: float | int | None
    threshold: str
    status: str  # "pass", "fail", "unknown"
    detail: str = ""


@dataclass(frozen=True)
class ProductEvaluationResult:
    decision: ProductDecision
    must_haves: dict[str, ProductMetric]
    should_haves: dict[str, ProductMetric]
    passed_must_haves: tuple[str, ...]
    failed_must_haves: tuple[str, ...]
    unknown_must_haves: tuple[str, ...]
    passed_should_groups: tuple[str, ...]
    triggered_stop_rules: tuple[str, ...]
    reasons: tuple[str, ...]


# Frozen Must-Have criteria (M1–M5) from docs/pilot/pilot-plan.md
FROZEN_MUST_HAVES = {
    # M1: Activation
    "M1_login_invitee_completion_rate": (0.60, ">=", "login_invitees_onboarding_completed"),
    "M1_onboarding_starter_completion_rate": (0.80, ">=", "onboarding_starters_completed"),
    # M2: Try-on Realism
    "M2_mean_vto_rating": (3.80, ">=", "mean_visual_rating_1_to_5"),
    "M2_ratings_gte_4_rate": (0.70, ">=", "ratings_4_or_5_percentage"),
    "M2_defect_rate": (0.15, "<=", "unnatural_or_drift_defect_flags"),
    # M3: Reliability
    "M3_crash_free_sessions": (0.99, ">=", "crash_free_mobile_sessions"),
    "M3_tryon_success_rate": (0.90, ">=", "user_visible_tryon_completion"),
    "M3_p95_latency_seconds": (45.0, "<=", "p95_end_to_end_queue_and_inference"),
    # M4: Trust & Privacy
    "M4_privacy_incident_count": (0, "<=", "security_or_privacy_incidents"),
    "M4_photo_comfort_agreement_rate": (0.80, ">=", "photo_comfort_survey_agreement"),
    "M4_consent_dropoff_rate": (0.10, "<=", "consent_screen_abandonment"),
    # M5: Return / Retention
    "M5_week2_return_rate": (0.50, ">=", "week2_days_7_to_13_retention"),
}

# Frozen Should-Have criteria (S1–S4) from docs/pilot/pilot-plan.md
FROZEN_SHOULD_HAVES = {
    "S1_feed_relevance_rating_gte_4_rate": (0.60, ">=", "S1"),
    "S1_negative_feed_signal_rate": (0.15, "<=", "S1"),
    "S2_week1_tryon_rate": (0.60, ">=", "S2"),
    "S2_median_tryons_per_user": (3.0, ">=", "S2"),
    "S2_median_minutes_to_first_tryon": (10.0, "<=", "S2"),
    "S3_buy_click_rate": (0.40, ">=", "S3"),
    "S3_verified_purchases": (3, ">=", "S3"),
    "S4_sus_score": (68.0, ">=", "S4"),
    "S4_pmf_very_disappointed_rate": (0.30, ">=", "S4"),
    "S4_nps_score": (20.0, ">=", "S4"),
}

STOP_RULES = (
    "stop_suspected_data_exposure",
    "stop_stability_crash_spike",
    "stop_tryon_outage_spike",
    "stop_api_5xx_wave",
    "stop_spend_budget_breach",
    "stop_privacy_discomfort_attrition",
    "stop_offensive_ai_output",
)


def evaluate_product_metrics(
    metrics_data: dict[str, Any], allow_synthetic: bool = False
) -> ProductEvaluationResult:
    """Evaluates pilot product metrics against frozen contract (docs/pilot/pilot-plan.md).

    Fail-closed:
    - Missing or unmeasured must-haves trigger HOLD.
    - Synthetic metrics fail closed unless explicitly allowed.
    - Triggered stop rules force HOLD / FIX.
    """
    if bool(metrics_data.get("is_synthetic", False)) and not allow_synthetic:
        return ProductEvaluationResult(
            decision=ProductDecision.HOLD,
            must_haves={},
            should_haves={},
            passed_must_haves=(),
            failed_must_haves=(),
            unknown_must_haves=tuple(FROZEN_MUST_HAVES.keys()),
            passed_should_groups=(),
            triggered_stop_rules=(),
            reasons=("synthetic_metrics_rejected_for_release_governance",),
        )

    evaluated_must: dict[str, ProductMetric] = {}
    passed_must: list[str] = []
    failed_must: list[str] = []
    unknown_must: list[str] = []
    reasons: list[str] = []

    # 1. Evaluate Must-Haves (M1–M5)
    for name, (thresh, op, desc) in FROZEN_MUST_HAVES.items():
        val = metrics_data.get(name)
        if val is None:
            unknown_must.append(name)
            reasons.append(f"must_have_{name}_missing")
            evaluated_must[name] = ProductMetric(
                name=name,
                value=None,
                threshold=f"{op} {thresh}",
                status="unknown",
                detail=f"missing_{desc}",
            )
            continue

        try:
            num_val = float(val) if not isinstance(val, int) else val
        except (ValueError, TypeError):
            unknown_must.append(name)
            reasons.append(f"must_have_{name}_invalid_number")
            evaluated_must[name] = ProductMetric(
                name=name,
                value=None,
                threshold=f"{op} {thresh}",
                status="unknown",
                detail="invalid_number",
            )
            continue

        is_pass = num_val >= thresh if op == ">=" else num_val <= thresh

        if is_pass:
            passed_must.append(name)
            evaluated_must[name] = ProductMetric(
                name=name,
                value=num_val,
                threshold=f"{op} {thresh}",
                status="pass",
                detail=desc,
            )
        else:
            failed_must.append(name)
            reasons.append(f"must_have_{name}_failed:{num_val}{op}{thresh}")
            evaluated_must[name] = ProductMetric(
                name=name,
                value=num_val,
                threshold=f"{op} {thresh}",
                status="fail",
                detail=f"value_{num_val}_failed_threshold_{thresh}",
            )

    # 2. Evaluate Should-Haves (S1–S4)
    evaluated_should: dict[str, ProductMetric] = {}
    should_groups_passed: dict[str, bool] = {"S1": True, "S2": True, "S3": True, "S4": True}
    should_groups_present: dict[str, bool] = {"S1": False, "S2": False, "S3": False, "S4": False}

    for name, (thresh, op, group) in FROZEN_SHOULD_HAVES.items():
        val = metrics_data.get(name)
        if val is None:
            should_groups_passed[group] = False
            continue
        try:
            num_val = float(val) if not isinstance(val, int) else val
            should_groups_present[group] = True
            is_pass = num_val >= thresh if op == ">=" else num_val <= thresh
            if not is_pass:
                should_groups_passed[group] = False
            evaluated_should[name] = ProductMetric(
                name=name,
                value=num_val,
                threshold=f"{op} {thresh}",
                status="pass" if is_pass else "fail",
                detail=f"group_{group}",
            )
        except (ValueError, TypeError):
            should_groups_passed[group] = False

    passed_groups = tuple(
        g for g in ("S1", "S2", "S3", "S4") if should_groups_present[g] and should_groups_passed[g]
    )

    # 3. Check Stop Rules
    triggered_stops: list[str] = []
    for stop_rule in STOP_RULES:
        if bool(metrics_data.get(stop_rule, False)):
            triggered_stops.append(stop_rule)
            reasons.append(f"stop_rule_triggered:{stop_rule}")

    # 4. Determine Governed Decision
    if triggered_stops:
        decision = ProductDecision.HOLD
    elif unknown_must:
        decision = ProductDecision.HOLD
    elif failed_must:
        # Check pivot criteria: M2 realism, M4 trust, or M5 retention < 25%
        m5_val = float(metrics_data.get("M5_week2_return_rate", 0.0))
        m2_failed = any("M2_" in f for f in failed_must)
        m4_failed = any("M4_" in f for f in failed_must)
        if (m2_failed and m4_failed) or (m5_val < 0.25):
            decision = ProductDecision.PIVOT_OR_STOP
        elif len(failed_must) <= 2:
            decision = ProductDecision.FIX_AND_RERUN
        else:
            decision = ProductDecision.PIVOT_OR_STOP
    elif len(passed_groups) >= 3:
        decision = ProductDecision.GO
    else:
        # Must-haves passed, but fewer than 3 of 4 should-have groups met
        decision = ProductDecision.FIX_AND_RERUN
        reasons.append(f"insufficient_should_have_groups:{len(passed_groups)}<3")

    return ProductEvaluationResult(
        decision=decision,
        must_haves=evaluated_must,
        should_haves=evaluated_should,
        passed_must_haves=tuple(passed_must),
        failed_must_haves=tuple(failed_must),
        unknown_must_haves=tuple(unknown_must),
        passed_should_groups=passed_groups,
        triggered_stop_rules=tuple(triggered_stops),
        reasons=tuple(reasons),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate RC13 Pre-Registered Pilot Metrics")
    parser.add_argument("--input", type=Path, required=True, help="Path to pilot metrics JSON file")
    parser.add_argument(
        "--allow-synthetic", action="store_true", help="Allow synthetic metrics for tests"
    )
    args = parser.parse_args()

    if not args.input.exists():
        print(f"Error: file not found {args.input}")
        return

    data = json.loads(args.input.read_text(encoding="utf-8"))
    res = evaluate_product_metrics(data, allow_synthetic=args.allow_synthetic)
    print(f"PILOT PRODUCT DECISION: {res.decision.value.upper()}")
    print(f"Passed Must-Haves ({len(res.passed_must_haves)}/{len(FROZEN_MUST_HAVES)}): {list(res.passed_must_haves)}")
    print(f"Failed Must-Haves: {list(res.failed_must_haves)}")
    print(f"Unknown/Missing Must-Haves: {list(res.unknown_must_haves)}")
    print(f"Passed Should Groups (>=3 needed): {list(res.passed_should_groups)}")
    if res.triggered_stop_rules:
        print(f"Triggered Stop Rules: {list(res.triggered_stop_rules)}")
    if res.reasons:
        print("Reasons:")
        for r in res.reasons:
            print(f"  - {r}")


if __name__ == "__main__":
    main()
