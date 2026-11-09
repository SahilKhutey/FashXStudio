"""RC11 Pre-registered closed beta pilot metric evaluator."""
from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import mean, median
from typing import Any


@dataclass(frozen=True)
class Metric:
    name: str
    value: float | int | None
    threshold: str
    passed: bool | None
    detail: str = ""


@dataclass(frozen=True)
class Evaluation:
    decision: str
    must_haves: tuple[Metric, ...]
    should_haves: tuple[Metric, ...]
    stop_reasons: tuple[str, ...]
    missing_evidence: tuple[str, ...]


def ratio(numerator: int, denominator: int) -> float | None:
    """Calculates ratio or returns None if denominator is zero or invalid."""
    if denominator <= 0:
        return None
    return numerator / float(denominator)


def percentile(values: list[float], p: float) -> float | None:
    """Calculates percentile using nearest rank method. Returns None if empty."""
    if p <= 0 or p > 1:
        raise ValueError("Percentile p must be in (0, 1]")
    if not values:
        return None
    sorted_vals = sorted(values)
    k = math.ceil(p * len(sorted_vals)) - 1
    idx = max(0, min(k, len(sorted_vals) - 1))
    return sorted_vals[idx]


def validate_snapshot(snapshot: dict[str, Any]) -> list[str]:
    """Validates presence of required pilot snapshot fields."""
    missing: list[str] = []
    required_paths = (
        ("metadata", "pilot_id"),
        ("metadata", "period_start"),
        ("metadata", "period_end"),
        ("metadata", "extracted_at"),
        ("metadata", "evidence_type"),
        ("metadata", "source_reference"),
        ("counts", "invited"),
        ("counts", "login_invitees"),
        ("counts", "onboarding_starters"),
        ("counts", "activated_users"),
        ("counts", "onboarding_completed"),
        ("counts", "consent_starters"),
        ("counts", "consent_abandoned"),
        ("counts", "eligible_week2_users"),
        ("counts", "week2_returned_users"),
        ("counts", "tryon_submitted"),
        ("counts", "tryon_completed"),
        ("counts", "crash_free_sessions"),
        ("counts", "total_sessions"),
        ("counts", "feed_cards_viewed"),
        ("counts", "negative_feed_signals"),
        ("counts", "week1_tryon_users"),
        ("counts", "buy_click_users"),
        ("counts", "verified_purchases"),
        ("counts", "privacy_incidents"),
        ("ratings", "tryon_realism"),
        ("ratings", "feed_relevance"),
        ("ratings", "comfort_uploading_photo"),
        ("ratings", "sus"),
        ("ratings", "pmf_very_disappointed"),
        ("ratings", "pmf_respondents"),
        ("ratings", "nps_promoters"),
        ("ratings", "nps_passives"),
        ("ratings", "nps_detractors"),
        ("tryon", "latency_ms"),
        ("tryon", "defect_flags"),
        ("tryon", "rated_outputs"),
        ("tryon", "tryons_per_activated_user"),
        ("tryon", "minutes_to_first_tryon"),
        ("safety", "offensive_output_incidents"),
        ("safety", "data_exposure_incidents"),
        ("safety", "unresolved_stop_rules"),
        ("safety", "vendor_spend_usd"),
        ("safety", "vendor_budget_usd"),
    )

    for section, field in required_paths:
        sec = snapshot.get(section)
        if not isinstance(sec, dict) or sec.get(field) is None:
            missing.append(f"{section}.{field}")

    return missing


def evaluate_pilot_snapshot(snapshot: dict[str, Any]) -> Evaluation:
    """Evaluates pilot snapshot according to the pre-registered frozen protocol."""
    missing = validate_snapshot(snapshot)
    if missing:
        return Evaluation(
            decision="INCOMPLETE_EVIDENCE",
            must_haves=(),
            should_haves=(),
            stop_reasons=(),
            missing_evidence=tuple(missing),
        )

    metadata = snapshot["metadata"]
    if metadata.get("evidence_type") != "real":
        return Evaluation(
            decision="INCOMPLETE_EVIDENCE",
            must_haves=(),
            should_haves=(),
            stop_reasons=("evidence_type_not_real",),
            missing_evidence=("metadata.evidence_type==real",),
        )

    counts = snapshot["counts"]
    ratings = snapshot["ratings"]
    tryon = snapshot["tryon"]
    safety = snapshot["safety"]

    # 1. Evaluate Hard Stop Rules
    stop_reasons: list[str] = []
    if safety.get("data_exposure_incidents", 0) > 0:
        stop_reasons.append("suspected_data_exposure")
    if counts.get("total_sessions", 0) > 0:
        crash_rate = ratio(counts.get("crash_free_sessions", 0), counts.get("total_sessions", 0))
        if crash_rate is not None and crash_rate < 0.98:
            stop_reasons.append("stability_crash_spike")
    if counts.get("tryon_submitted", 0) > 0:
        tryon_fail_rate = 1.0 - (counts.get("tryon_completed", 0) / float(counts.get("tryon_submitted", 1)))
        if tryon_fail_rate > 0.25:
            stop_reasons.append("tryon_outage_spike")
    if safety.get("vendor_budget_usd", 0) > 0:
        spend_ratio = safety.get("vendor_spend_usd", 0) / float(safety.get("vendor_budget_usd", 1))
        if spend_ratio > 0.80:
            stop_reasons.append("spend_budget_breach")
    if safety.get("offensive_output_incidents", 0) > 0:
        stop_reasons.append("offensive_ai_output")
    if safety.get("unresolved_stop_rules", 0) > 0:
        stop_reasons.append("unresolved_stop_rules_present")

    # 2. Evaluate Must-Haves (M1-M5)
    must_haves: list[Metric] = []

    # M1: Activation
    m1_act_ratio = ratio(counts["activated_users"], counts["login_invitees"])
    m1_onb_ratio = ratio(counts["onboarding_completed"], counts["onboarding_starters"])
    m1_passed = (
        m1_act_ratio is not None
        and m1_act_ratio >= 0.60
        and m1_onb_ratio is not None
        and m1_onb_ratio >= 0.80
    )
    must_haves.append(
        Metric(
            name="M1_activation",
            value=m1_act_ratio,
            threshold="login_act>=0.60 and onb_comp>=0.80",
            passed=m1_passed,
            detail=f"act_rate={m1_act_ratio}, onb_rate={m1_onb_ratio}",
        )
    )

    # M2: Try-on Realism
    realism_vals = ratings["tryon_realism"]
    if realism_vals:
        mean_realism = mean(realism_vals)
        share_ge4 = sum(1 for r in realism_vals if r >= 4) / float(len(realism_vals))
    else:
        mean_realism = None
        share_ge4 = None

    defect_rate = ratio(tryon["defect_flags"], tryon["rated_outputs"])
    m2_passed = (
        mean_realism is not None
        and mean_realism >= 3.8
        and share_ge4 is not None
        and share_ge4 >= 0.70
        and defect_rate is not None
        and defect_rate <= 0.15
    )
    must_haves.append(
        Metric(
            name="M2_tryon_realism",
            value=mean_realism,
            threshold="mean>=3.8, ge4>=0.70, defects<=0.15",
            passed=m2_passed,
            detail=f"mean={mean_realism}, ge4_share={share_ge4}, defects={defect_rate}",
        )
    )

    # M3: Reliability
    crash_free = ratio(counts["crash_free_sessions"], counts["total_sessions"])
    tryon_success = ratio(counts["tryon_completed"], counts["tryon_submitted"])
    p95_lat = percentile(tryon["latency_ms"], 0.95)
    m3_passed = (
        crash_free is not None
        and crash_free >= 0.990
        and tryon_success is not None
        and tryon_success >= 0.900
        and p95_lat is not None
        and p95_lat <= 45000
    )
    must_haves.append(
        Metric(
            name="M3_reliability",
            value=crash_free,
            threshold="crash_free>=0.99, success>=0.90, p95<=45s",
            passed=m3_passed,
            detail=f"crash_free={crash_free}, success={tryon_success}, p95_ms={p95_lat}",
        )
    )

    # M4: Trust & Privacy
    incidents = counts["privacy_incidents"]
    comfort_vals = ratings["comfort_uploading_photo"]
    comfort_rate = (
        sum(1 for r in comfort_vals if r >= 4) / float(len(comfort_vals))
        if comfort_vals
        else None
    )
    consent_drop = ratio(counts["consent_abandoned"], counts["consent_starters"])
    m4_passed = (
        incidents == 0
        and comfort_rate is not None
        and comfort_rate >= 0.80
        and consent_drop is not None
        and consent_drop <= 0.10
    )
    must_haves.append(
        Metric(
            name="M4_trust_and_privacy",
            value=comfort_rate,
            threshold="incidents==0, comfort>=0.80, consent_drop<=0.10",
            passed=m4_passed,
            detail=f"incidents={incidents}, comfort={comfort_rate}, drop={consent_drop}",
        )
    )

    # M5: Return (Retention)
    ret_rate = ratio(counts["week2_returned_users"], counts["eligible_week2_users"])
    m5_passed = ret_rate is not None and ret_rate >= 0.50
    must_haves.append(
        Metric(
            name="M5_retention_week2",
            value=ret_rate,
            threshold="week2_ret>=0.50",
            passed=m5_passed,
            detail=f"ret_rate={ret_rate}",
        )
    )

    # 3. Evaluate Should-Haves (S1-S4)
    should_haves: list[Metric] = []

    # S1: Feed Relevance
    feed_vals = ratings["feed_relevance"]
    feed_ge4 = (
        sum(1 for r in feed_vals if r >= 4) / float(len(feed_vals))
        if feed_vals
        else None
    )
    neg_signals = ratio(counts["negative_feed_signals"], counts["feed_cards_viewed"])
    s1_passed = feed_ge4 is not None and feed_ge4 >= 0.60 and neg_signals is not None and neg_signals <= 0.15
    should_haves.append(
        Metric(
            name="S1_feed_relevance",
            value=feed_ge4,
            threshold="ge4>=0.60 and neg_signals<=0.15",
            passed=s1_passed,
            detail=f"ge4_share={feed_ge4}, neg_signals={neg_signals}",
        )
    )

    # S2: Engagement
    w1_share = ratio(counts["week1_tryon_users"], counts["activated_users"])
    tryon_counts = tryon["tryons_per_activated_user"]
    med_tryons = median(tryon_counts) if tryon_counts else None
    min_to_first = tryon["minutes_to_first_tryon"]
    med_min = median(min_to_first) if min_to_first else None
    s2_passed = (
        w1_share is not None
        and w1_share >= 0.60
        and med_tryons is not None
        and med_tryons >= 3.0
        and med_min is not None
        and med_min <= 10.0
    )
    should_haves.append(
        Metric(
            name="S2_engagement",
            value=w1_share,
            threshold="w1_share>=0.60, med_tryons>=3, med_min<=10",
            passed=s2_passed,
            detail=f"w1_share={w1_share}, med_tryons={med_tryons}, med_min={med_min}",
        )
    )

    # S3: Purchase Intent
    buy_share = ratio(counts["buy_click_users"], counts["activated_users"])
    purchases = counts["verified_purchases"]
    s3_passed = buy_share is not None and buy_share >= 0.40 and purchases >= 3
    should_haves.append(
        Metric(
            name="S3_purchase_intent",
            value=buy_share,
            threshold="buy_clicks>=0.40 and purchases>=3",
            passed=s3_passed,
            detail=f"buy_share={buy_share}, purchases={purchases}",
        )
    )

    # S4: Satisfaction
    sus_vals = ratings["sus"]
    mean_sus = mean(sus_vals) if sus_vals else None
    pmf_ratio = ratio(ratings["pmf_very_disappointed"], ratings["pmf_respondents"])
    total_nps = ratings["nps_promoters"] + ratings["nps_passives"] + ratings["nps_detractors"]
    nps = (
        ((ratings["nps_promoters"] - ratings["nps_detractors"]) / float(total_nps)) * 100.0
        if total_nps > 0
        else None
    )
    s4_passed = (
        mean_sus is not None
        and mean_sus >= 68.0
        and pmf_ratio is not None
        and pmf_ratio >= 0.30
        and nps is not None
        and nps >= 20.0
    )
    should_haves.append(
        Metric(
            name="S4_satisfaction",
            value=mean_sus,
            threshold="sus>=68, pmf>=0.30, nps>=20",
            passed=s4_passed,
            detail=f"sus={mean_sus}, pmf={pmf_ratio}, nps={nps}",
        )
    )

    # 4. Decision Rule
    if stop_reasons:
        decision = "HOLD_SAFETY_TRIGGERED"
    else:
        m_passed_count = sum(1 for m in must_haves if m.passed is True)
        s_passed_count = sum(1 for s in should_haves if s.passed is True)

        if m_passed_count == 5 and s_passed_count >= 3:
            decision = "GO_REVIEW_REQUIRED"
        elif m_passed_count in (3, 4) and s_passed_count >= 2:
            decision = "FIX_AND_RERUN"
        elif (
            (must_haves[1].passed is False)  # M2 realism
            or (must_haves[3].passed is False)  # M4 trust
            or (ret_rate is not None and ret_rate < 0.25)
        ):
            decision = "PIVOT_OR_STOP"
        else:
            decision = "HOLD"

    return Evaluation(
        decision=decision,
        must_haves=tuple(must_haves),
        should_haves=tuple(should_haves),
        stop_reasons=tuple(stop_reasons),
        missing_evidence=(),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate RC11 Pilot Snapshot")
    parser.add_argument("snapshot_path", type=Path, help="Path to pilot_snapshot.json")
    args = parser.parse_args()

    if not args.snapshot_path.exists():
        print(f"Error: Snapshot not found at {args.snapshot_path}")
        return

    data = json.loads(args.snapshot_path.read_text(encoding="utf-8"))
    evaluation = evaluate_pilot_snapshot(data)
    print(json.dumps(asdict(evaluation), indent=2))


if __name__ == "__main__":
    main()
