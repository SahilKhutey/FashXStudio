"""RC13 Product Validation and Pilot Metric Evaluator."""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any


class ProductDecision(StrEnum):
    PASS = "pass"
    FAIL = "fail"
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
    metrics: dict[str, ProductMetric]
    passed: tuple[str, ...]
    failed: tuple[str, ...]
    unknown: tuple[str, ...]
    reasons: tuple[str, ...]


REQUIRED_METRIC_SPECS = {
    "activation_login_rate": (0.70, ">="),
    "tryon_completion_rate": (0.60, ">="),
    "vto_mean_rating": (3.50, ">="),
    "crash_free_sessions": (0.99, ">="),
    "privacy_incident_count": (0, "<="),
}

OPTIONAL_METRIC_SPECS = {
    "week2_retention_rate": (0.20, ">="),
    "retailer_clickout_rate": (0.15, ">="),
}


def evaluate_product_metrics(
    metrics_data: dict[str, Any], allow_synthetic: bool = False
) -> ProductEvaluationResult:
    """Evaluates product metrics against pre-registered targets.

    Fail-closed: Missing metrics evaluate to UNKNOWN and trigger a HOLD decision.
    """
    if bool(metrics_data.get("is_synthetic", False)) and not allow_synthetic:
        return ProductEvaluationResult(
            decision=ProductDecision.HOLD,
            metrics={},
            passed=(),
            failed=(),
            unknown=tuple(REQUIRED_METRIC_SPECS.keys()),
            reasons=("synthetic_metrics_rejected",),
        )

    evaluated: dict[str, ProductMetric] = {}
    passed: list[str] = []
    failed: list[str] = []
    unknown: list[str] = []
    reasons: list[str] = []

    # Evaluate required metrics
    for name, (thresh, op) in REQUIRED_METRIC_SPECS.items():
        val = metrics_data.get(name)
        if val is None:
            unknown.append(name)
            reasons.append(f"metric_{name}_missing")
            evaluated[name] = ProductMetric(
                name=name,
                value=None,
                threshold=f"{op} {thresh}",
                status="unknown",
                detail="missing_data",
            )
            continue

        try:
            num_val = float(val) if not isinstance(val, int) else val
        except (ValueError, TypeError):
            unknown.append(name)
            reasons.append(f"metric_{name}_invalid_number")
            evaluated[name] = ProductMetric(
                name=name,
                value=None,
                threshold=f"{op} {thresh}",
                status="unknown",
                detail="invalid_number",
            )
            continue

        is_pass = False
        if op == ">=":
            is_pass = num_val >= thresh
        elif op == "<=":
            is_pass = num_val <= thresh

        if is_pass:
            passed.append(name)
            evaluated[name] = ProductMetric(
                name=name,
                value=num_val,
                threshold=f"{op} {thresh}",
                status="pass",
                detail="meets_threshold",
            )
        else:
            failed.append(name)
            reasons.append(f"metric_{name}_below_threshold:{num_val}<{thresh}")
            evaluated[name] = ProductMetric(
                name=name,
                value=num_val,
                threshold=f"{op} {thresh}",
                status="fail",
                detail=f"value_{num_val}_failed_threshold_{thresh}",
            )

    # Evaluate optional metrics if present
    for name, (thresh, op) in OPTIONAL_METRIC_SPECS.items():
        val = metrics_data.get(name)
        if val is None:
            continue
        try:
            num_val = float(val) if not isinstance(val, int) else val
            is_pass = num_val >= thresh if op == ">=" else num_val <= thresh
            status = "pass" if is_pass else "fail"
            evaluated[name] = ProductMetric(
                name=name,
                value=num_val,
                threshold=f"{op} {thresh}",
                status=status,
                detail=f"optional_metric_{status}",
            )
        except (ValueError, TypeError):
            continue

    if failed:
        decision = ProductDecision.FAIL
    elif unknown:
        decision = ProductDecision.HOLD
    else:
        decision = ProductDecision.PASS

    return ProductEvaluationResult(
        decision=decision,
        metrics=evaluated,
        passed=tuple(passed),
        failed=tuple(failed),
        unknown=tuple(unknown),
        reasons=tuple(reasons),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate RC13 Product Metrics")
    parser.add_argument("--input", type=Path, required=True, help="Path to metrics JSON file")
    parser.add_argument(
        "--allow-synthetic", action="store_true", help="Allow synthetic metrics"
    )
    args = parser.parse_args()

    if not args.input.exists():
        print(f"Error: file not found {args.input}")
        return

    data = json.loads(args.input.read_text(encoding="utf-8"))
    res = evaluate_product_metrics(data, allow_synthetic=args.allow_synthetic)
    print(f"PRODUCT EVALUATION DECISION: {res.decision.value.upper()}")
    print(f"Passed: {list(res.passed)}")
    print(f"Failed: {list(res.failed)}")
    print(f"Unknown: {list(res.unknown)}")
    if res.reasons:
        print("Reasons:")
        for r in res.reasons:
            print(f"  - {r}")


if __name__ == "__main__":
    main()
