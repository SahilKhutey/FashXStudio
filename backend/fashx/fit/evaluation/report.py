"""Versioned evaluation report and release-gate checker (Phase 08.3 - Task 8.3.11)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from fashx.fit.evaluation.metrics import EvaluationCase, evaluate_cases


@dataclass(frozen=True)
class ReleaseGateCheck:
    """Single Phase 08.3 release gate check result."""

    gate_name: str
    threshold: str
    observed: str
    passed: bool


@dataclass(frozen=True)
class EvaluationReport:
    """Reproducible evaluation report bound to dataset and algorithm versions."""

    dataset_version: str
    fit_algorithm_version: str
    category_policy_version: str
    generated_at: datetime
    metrics: dict[str, object]
    gates: tuple[ReleaseGateCheck, ...]
    all_gates_passed: bool


def build_evaluation_report(
    *,
    dataset_version: str,
    fit_algorithm_version: str,
    category_policy_version: str,
    cases: list[EvaluationCase],
) -> EvaluationReport:
    """Evaluate all cases against Phase 08.3 proposed release gates."""
    metrics = evaluate_cases(cases)
    false_rate = metrics.get("false_recommendation_rate")
    exact_acc = metrics.get("exact_size_accuracy")
    accept_acc = metrics.get("acceptable_size_accuracy")
    req_violations = int(metrics.get("required_evidence_violations", 0))  # type: ignore[arg-type]
    unsup_cat = int(metrics.get("unsupported_category_recommendations", 0))  # type: ignore[arg-type]
    unauth_chart = int(metrics.get("unauthorized_chart_uses", 0))  # type: ignore[arg-type]
    stale_chart = int(metrics.get("stale_chart_recommendations", 0))  # type: ignore[arg-type]

    gates = (
        ReleaseGateCheck(
            gate_name="False recommendation rate",
            threshold="<= 0.05",
            observed=str(false_rate),
            passed=(false_rate is None) or (float(false_rate) <= 0.05),  # type: ignore[arg-type]
        ),
        ReleaseGateCheck(
            gate_name="Exact-size accuracy among recommendations",
            threshold=">= 0.80",
            observed=str(exact_acc),
            passed=(exact_acc is None) or (float(exact_acc) >= 0.80),  # type: ignore[arg-type]
        ),
        ReleaseGateCheck(
            gate_name="Acceptable-size accuracy",
            threshold=">= 0.90",
            observed=str(accept_acc),
            passed=(accept_acc is None) or (float(accept_acc) >= 0.90),  # type: ignore[arg-type]
        ),
        ReleaseGateCheck(
            gate_name="Required-evidence violations",
            threshold="== 0",
            observed=str(req_violations),
            passed=req_violations == 0,
        ),
        ReleaseGateCheck(
            gate_name="Unsupported category recommendations",
            threshold="== 0",
            observed=str(unsup_cat),
            passed=unsup_cat == 0,
        ),
        ReleaseGateCheck(
            gate_name="Unauthorized chart use",
            threshold="== 0",
            observed=str(unauth_chart),
            passed=unauth_chart == 0,
        ),
        ReleaseGateCheck(
            gate_name="Stale chart recommendations",
            threshold="== 0",
            observed=str(stale_chart),
            passed=stale_chart == 0,
        ),
    )

    return EvaluationReport(
        dataset_version=dataset_version,
        fit_algorithm_version=fit_algorithm_version,
        category_policy_version=category_policy_version,
        generated_at=datetime.now(UTC),
        metrics=metrics,
        gates=gates,
        all_gates_passed=all(g.passed for g in gates),
    )
