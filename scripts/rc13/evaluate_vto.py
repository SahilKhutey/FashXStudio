"""RC13 Virtual Try-On (VTO) Quality and Latency Evaluator.

Reconciled with docs/pilot/pilot-plan.md (M2, M3) and docs/release/gates.md (Gate G5).
Distinguishes between contractual release gate ceilings and internal operational targets.
"""
from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from statistics import mean
from typing import Any

DEFECT_TAGS: tuple[str, ...] = (
    "artifacts_detected",
    "body_distortion",
    "garment_mismatch",
    "identity_drift",
    "blur_defect",
)

# Contractual Release Gate Standards (docs/pilot/pilot-plan.md M2/M3 & docs/release/gates.md G5)
GATE_MIN_COMPLETION_RATE = 0.90   # >= 90.0% completion rate (pilot plan M3)
GATE_MAX_DEFECT_RATE = 0.15       # <= 15.0% distinct defective jobs (pilot plan M2)
GATE_MAX_P95_LATENCY = 45.0       # <= 45.0s end-to-end P95 latency (pilot plan M3 & gates.md G5)
GATE_MIN_MEAN_RATING = 3.80       # >= 3.80 / 5.0 mean user rating (pilot plan M2)

# Internal Operational Excellence Targets
TARGET_MIN_COMPLETION_RATE = 0.95
TARGET_MAX_DEFECT_RATE = 0.10
TARGET_MAX_P95_LATENCY = 30.0
TARGET_MIN_MEAN_RATING = 4.00


class VTODecision(StrEnum):
    PASS = "pass"
    FAIL = "fail"
    HOLD = "hold"


@dataclass(frozen=True)
class VTOEvaluationResult:
    decision: VTODecision
    meets_operational_targets: bool
    total_jobs: int
    completed_jobs: int
    defective_jobs_count: int
    completion_rate: float | None
    defect_job_rate: float | None
    p95_latency_seconds: float | None
    mean_rating: float | None
    passed_gate_checks: tuple[str, ...]
    failed_gate_checks: tuple[str, ...]
    passed_operational_targets: tuple[str, ...]
    reasons: tuple[str, ...]


def calculate_percentile(values: list[float], p: float) -> float | None:
    """Calculates percentile using nearest rank method."""
    if not values:
        return None
    if p <= 0 or p > 1:
        raise ValueError("Percentile p must be in (0, 1]")
    sorted_vals = sorted(values)
    k = math.ceil(p * len(sorted_vals)) - 1
    idx = max(0, min(k, len(sorted_vals) - 1))
    return sorted_vals[idx]


def evaluate_vto_jobs(
    jobs: list[dict[str, Any]], require_real_provider: bool = True
) -> VTOEvaluationResult:
    """Evaluates VTO jobs against reconciled gate criteria and operational targets.

    Deduplicates defects across jobs: a job with multiple defect flags counts as 1 defective job.
    Fails closed if mock/synthetic providers are passed when real provider is required.
    """
    if not jobs:
        return VTOEvaluationResult(
            decision=VTODecision.HOLD,
            meets_operational_targets=False,
            total_jobs=0,
            completed_jobs=0,
            defective_jobs_count=0,
            completion_rate=None,
            defect_job_rate=None,
            p95_latency_seconds=None,
            mean_rating=None,
            passed_gate_checks=(),
            failed_gate_checks=("no_jobs_provided",),
            passed_operational_targets=(),
            reasons=("empty_vto_job_list",),
        )

    if require_real_provider:
        for idx, job in enumerate(jobs):
            provider = str(job.get("provider", "")).strip().lower()
            is_synthetic = bool(job.get("is_synthetic", False))
            if provider in {"mock", "synthetic", "test", ""} or is_synthetic:
                return VTOEvaluationResult(
                    decision=VTODecision.HOLD,
                    meets_operational_targets=False,
                    total_jobs=len(jobs),
                    completed_jobs=0,
                    defective_jobs_count=0,
                    completion_rate=None,
                    defect_job_rate=None,
                    p95_latency_seconds=None,
                    mean_rating=None,
                    passed_gate_checks=(),
                    failed_gate_checks=("provider_validation",),
                    passed_operational_targets=(),
                    reasons=(f"mock_or_synthetic_provider_detected_at_job_{idx}:{provider}",),
                )

    total_jobs = len(jobs)
    completed = [j for j in jobs if str(j.get("status", "")).strip().lower() == "completed"]
    completed_count = len(completed)
    completion_rate = completed_count / total_jobs

    # Deduplicated defect counting
    defective_jobs = [
        j
        for j in completed
        if any(bool(j.get(tag)) for tag in DEFECT_TAGS)
    ]
    defective_count = len(defective_jobs)
    defect_rate = (defective_count / completed_count) if completed_count > 0 else 0.0

    # Latencies
    latencies = [
        float(j["latency_seconds"])
        for j in completed
        if j.get("latency_seconds") is not None
    ]
    p95_latency = calculate_percentile(latencies, 0.95)

    # Ratings
    ratings = [
        float(j["rating"])
        for j in completed
        if j.get("rating") is not None
    ]
    avg_rating = mean(ratings) if ratings else None

    passed_gate: list[str] = []
    failed_gate: list[str] = []
    passed_targets: list[str] = []
    reasons: list[str] = []

    # 1. Completion Rate (Gate: >= 0.90, Target: >= 0.95)
    if completion_rate >= GATE_MIN_COMPLETION_RATE:
        passed_gate.append("completion_rate")
        if completion_rate >= TARGET_MIN_COMPLETION_RATE:
            passed_targets.append("completion_rate")
    else:
        failed_gate.append("completion_rate")
        reasons.append(f"completion_rate_below_gate:{completion_rate:.3f}<{GATE_MIN_COMPLETION_RATE}")

    # 2. Defect Rate (Gate: <= 0.15, Target: <= 0.10)
    if defect_rate <= GATE_MAX_DEFECT_RATE:
        passed_gate.append("defect_rate")
        if defect_rate <= TARGET_MAX_DEFECT_RATE:
            passed_targets.append("defect_rate")
    else:
        failed_gate.append("defect_rate")
        reasons.append(f"defect_rate_exceeded_gate:{defect_rate:.3f}>{GATE_MAX_DEFECT_RATE}")

    # 3. P95 Latency (Gate: <= 45.0s, Target: <= 30.0s)
    if p95_latency is not None and p95_latency <= GATE_MAX_P95_LATENCY:
        passed_gate.append("p95_latency")
        if p95_latency <= TARGET_MAX_P95_LATENCY:
            passed_targets.append("p95_latency")
    elif p95_latency is not None:
        failed_gate.append("p95_latency")
        reasons.append(f"p95_latency_exceeded_gate:{p95_latency:.2f}>{GATE_MAX_P95_LATENCY}s")
    else:
        failed_gate.append("p95_latency")
        reasons.append("p95_latency_missing")

    # 4. Rating (Gate: >= 3.80, Target: >= 4.00 if present)
    if avg_rating is not None:
        if avg_rating >= GATE_MIN_MEAN_RATING:
            passed_gate.append("mean_rating")
            if avg_rating >= TARGET_MIN_MEAN_RATING:
                passed_targets.append("mean_rating")
        else:
            failed_gate.append("mean_rating")
            reasons.append(f"mean_rating_below_gate:{avg_rating:.2f}<{GATE_MIN_MEAN_RATING}")

    decision = VTODecision.FAIL if failed_gate else VTODecision.PASS
    meets_all_targets = len(passed_targets) == len(passed_gate) and not failed_gate

    return VTOEvaluationResult(
        decision=decision,
        meets_operational_targets=meets_all_targets,
        total_jobs=total_jobs,
        completed_jobs=completed_count,
        defective_jobs_count=defective_count,
        completion_rate=completion_rate,
        defect_job_rate=defect_rate,
        p95_latency_seconds=p95_latency,
        mean_rating=avg_rating,
        passed_gate_checks=tuple(passed_gate),
        failed_gate_checks=tuple(failed_gate),
        passed_operational_targets=tuple(passed_targets),
        reasons=tuple(reasons),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate RC13 VTO Jobs (Reconciled Standards)")
    parser.add_argument("--input", type=Path, required=True, help="Path to VTO jobs JSON")
    parser.add_argument(
        "--allow-mock", action="store_true", help="Allow mock provider for testing"
    )
    args = parser.parse_args()

    if not args.input.exists():
        print(f"Error: file not found {args.input}")
        return

    data = json.loads(args.input.read_text(encoding="utf-8"))
    jobs = data if isinstance(data, list) else data.get("jobs", [])
    result = evaluate_vto_jobs(jobs, require_real_provider=not args.allow_mock)
    print(f"VTO EVALUATION DECISION: {result.decision.value.upper()}")
    print(f"Meets Operational Targets (stricter): {result.meets_operational_targets}")
    print(f"Total Jobs: {result.total_jobs}, Completed: {result.completed_jobs}, Defective: {result.defective_jobs_count}")
    print(f"Passed Gate Checks: {list(result.passed_gate_checks)}")
    print(f"Failed Gate Checks: {list(result.failed_gate_checks)}")
    print(f"Passed Operational Targets: {list(result.passed_operational_targets)}")
    if result.reasons:
        print("Reasons:")
        for r in result.reasons:
            print(f"  - {r}")


if __name__ == "__main__":
    main()
