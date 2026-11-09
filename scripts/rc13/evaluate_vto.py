"""RC13 Virtual Try-On (VTO) Quality and Latency Evaluator."""
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

MIN_COMPLETION_RATE = 0.95
MAX_DEFECT_RATE = 0.15
MAX_P95_LATENCY = 30.0
MIN_MEAN_RATING = 3.50


class VTODecision(StrEnum):
    PASS = "pass"
    FAIL = "fail"
    HOLD = "hold"


@dataclass(frozen=True)
class VTOEvaluationResult:
    decision: VTODecision
    total_jobs: int
    completed_jobs: int
    defective_jobs_count: int
    completion_rate: float | None
    defect_job_rate: float | None
    p95_latency_seconds: float | None
    mean_rating: float | None
    passed_checks: tuple[str, ...]
    failed_checks: tuple[str, ...]
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
    """Evaluates VTO jobs against quality, defect, and latency thresholds.

    Deduplicates defects across jobs: a job with multiple defect flags counts as 1 defective job.
    Fails closed if mock/synthetic providers are passed when real provider is required.
    """
    if not jobs:
        return VTOEvaluationResult(
            decision=VTODecision.HOLD,
            total_jobs=0,
            completed_jobs=0,
            defective_jobs_count=0,
            completion_rate=None,
            defect_job_rate=None,
            p95_latency_seconds=None,
            mean_rating=None,
            passed_checks=(),
            failed_checks=("no_jobs_provided",),
            reasons=("empty_vto_job_list",),
        )

    if require_real_provider:
        for idx, job in enumerate(jobs):
            provider = str(job.get("provider", "")).strip().lower()
            is_synthetic = bool(job.get("is_synthetic", False))
            if provider in {"mock", "synthetic", "test", ""} or is_synthetic:
                return VTOEvaluationResult(
                    decision=VTODecision.HOLD,
                    total_jobs=len(jobs),
                    completed_jobs=0,
                    defective_jobs_count=0,
                    completion_rate=None,
                    defect_job_rate=None,
                    p95_latency_seconds=None,
                    mean_rating=None,
                    passed_checks=(),
                    failed_checks=("provider_validation",),
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

    passed_checks: list[str] = []
    failed_checks: list[str] = []
    reasons: list[str] = []

    # Check 1: Completion rate >= 0.95
    if completion_rate >= MIN_COMPLETION_RATE:
        passed_checks.append("completion_rate")
    else:
        failed_checks.append("completion_rate")
        reasons.append(f"completion_rate_below_min:{completion_rate:.3f}<{MIN_COMPLETION_RATE}")

    # Check 2: Defect rate <= 0.15
    if defect_rate <= MAX_DEFECT_RATE:
        passed_checks.append("defect_rate")
    else:
        failed_checks.append("defect_rate")
        reasons.append(f"defect_rate_exceeded:{defect_rate:.3f}>{MAX_DEFECT_RATE}")

    # Check 3: P95 latency <= 30.0s
    if p95_latency is not None and p95_latency <= MAX_P95_LATENCY:
        passed_checks.append("p95_latency")
    elif p95_latency is not None:
        failed_checks.append("p95_latency")
        reasons.append(f"p95_latency_exceeded:{p95_latency:.2f}>{MAX_P95_LATENCY}s")
    else:
        failed_checks.append("p95_latency")
        reasons.append("p95_latency_missing")

    # Check 4: Rating >= 3.50 if present
    if avg_rating is not None:
        if avg_rating >= MIN_MEAN_RATING:
            passed_checks.append("mean_rating")
        else:
            failed_checks.append("mean_rating")
            reasons.append(f"mean_rating_below_min:{avg_rating:.2f}<{MIN_MEAN_RATING}")

    decision = VTODecision.FAIL if failed_checks else VTODecision.PASS

    return VTOEvaluationResult(
        decision=decision,
        total_jobs=total_jobs,
        completed_jobs=completed_count,
        defective_jobs_count=defective_count,
        completion_rate=completion_rate,
        defect_job_rate=defect_rate,
        p95_latency_seconds=p95_latency,
        mean_rating=avg_rating,
        passed_checks=tuple(passed_checks),
        failed_checks=tuple(failed_checks),
        reasons=tuple(reasons),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate RC13 VTO Jobs")
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
    print(f"Total Jobs: {result.total_jobs}, Completed: {result.completed_jobs}, Defective: {result.defective_jobs_count}")
    print(f"Passed Checks: {list(result.passed_checks)}")
    print(f"Failed Checks: {list(result.failed_checks)}")
    if result.reasons:
        print("Reasons:")
        for r in result.reasons:
            print(f"  - {r}")


if __name__ == "__main__":
    main()
