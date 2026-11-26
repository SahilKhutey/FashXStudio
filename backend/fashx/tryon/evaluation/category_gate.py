"""Category quality gate and release policy enforcement for Virtual Try-On.

Release Policy:
A garment category is eligible for customer-facing try-on ONLY when it meets
the rigorous CategoryGateThresholds.

State Transitions:
NOT_EVALUATED -> EVALUATING -> APPROVED_LIMITED / NEEDS_IMPROVEMENT / BLOCKED
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from fashx.tryon.evaluation.contracts import CategoryStatus

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CategoryMetrics:
    """Consolidated benchmark quality metrics for a single garment category."""

    category: str
    sample_count: int
    job_success_rate: float
    garment_preservation: float
    body_alignment: float
    artifact_quality: float
    identity_preservation: float
    visual_plausibility: float
    non_misleading: float
    reviewer_rejection_rate: float
    critical_misleading_count: int


@dataclass(frozen=True)
class CategoryGateThresholds:
    """Acceptance standards required for a garment category to be approved."""

    minimum_sample_count: int = 30
    minimum_success_rate: float = 0.90
    minimum_garment_preservation: float = 3.8
    minimum_body_alignment: float = 3.8
    minimum_artifact_quality: float = 3.8
    minimum_identity_preservation: float = 4.0
    minimum_visual_plausibility: float = 3.8
    minimum_non_misleading: float = 4.0
    maximum_rejection_rate: float = 0.05
    max_critical_misleading: int = 0


@dataclass(frozen=True)
class GateEvaluationResult:
    """Outcome of category gate evaluation."""

    category: str
    passed: bool
    status: CategoryStatus
    failures: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def evaluate_category(
    metrics: CategoryMetrics,
    thresholds: CategoryGateThresholds | None = None,
) -> GateEvaluationResult:
    """Evaluate category benchmark metrics against acceptance thresholds."""
    th = thresholds or CategoryGateThresholds()
    failures: list[str] = []
    warnings: list[str] = []

    # 1. Sample Size Gate
    if metrics.sample_count < th.minimum_sample_count:
        failures.append(
            f"Insufficient sample count: {metrics.sample_count} < minimum {th.minimum_sample_count}"
        )
        return GateEvaluationResult(
            category=metrics.category,
            passed=False,
            status=CategoryStatus.EVALUATING,
            failures=failures,
        )

    # 2. Critical Misleading Hard Stop Gate
    if metrics.critical_misleading_count > th.max_critical_misleading:
        failures.append(
            f"Critical misleading outputs detected ({metrics.critical_misleading_count} > {th.max_critical_misleading})"
        )
        return GateEvaluationResult(
            category=metrics.category,
            passed=False,
            status=CategoryStatus.BLOCKED,
            failures=failures,
        )

    # 3. Job Success Rate
    if metrics.job_success_rate < th.minimum_success_rate:
        failures.append(
            f"Job success rate {metrics.job_success_rate:.2f} < threshold {th.minimum_success_rate:.2f}"
        )

    # 4. Dimension Scores
    if metrics.garment_preservation < th.minimum_garment_preservation:
        failures.append(
            f"Garment preservation {metrics.garment_preservation:.2f} < threshold {th.minimum_garment_preservation:.2f}"
        )

    if metrics.body_alignment < th.minimum_body_alignment:
        failures.append(
            f"Body alignment {metrics.body_alignment:.2f} < threshold {th.minimum_body_alignment:.2f}"
        )

    if metrics.artifact_quality < th.minimum_artifact_quality:
        failures.append(
            f"Artifact quality {metrics.artifact_quality:.2f} < threshold {th.minimum_artifact_quality:.2f}"
        )

    if metrics.identity_preservation < th.minimum_identity_preservation:
        failures.append(
            f"Identity preservation {metrics.identity_preservation:.2f} < threshold {th.minimum_identity_preservation:.2f}"
        )

    if metrics.visual_plausibility < th.minimum_visual_plausibility:
        failures.append(
            f"Visual plausibility {metrics.visual_plausibility:.2f} < threshold {th.minimum_visual_plausibility:.2f}"
        )

    if metrics.non_misleading < th.minimum_non_misleading:
        failures.append(
            f"Non-misleading score {metrics.non_misleading:.2f} < threshold {th.minimum_non_misleading:.2f}"
        )

    # 5. Reviewer Rejection Rate
    if metrics.reviewer_rejection_rate > th.maximum_rejection_rate:
        failures.append(
            f"Reviewer rejection rate {metrics.reviewer_rejection_rate:.2f} > ceiling {th.maximum_rejection_rate:.2f}"
        )

    passed = len(failures) == 0
    status = CategoryStatus.APPROVED_LIMITED if passed else CategoryStatus.NEEDS_IMPROVEMENT

    if passed:
        logger.info("Category %s PASSED quality gates -> APPROVED_LIMITED", metrics.category)
    else:
        logger.warning(
            "Category %s FAILED quality gates (%d issues) -> %s",
            metrics.category,
            len(failures),
            status.value,
        )

    return GateEvaluationResult(
        category=metrics.category,
        passed=passed,
        status=status,
        failures=failures,
        warnings=warnings,
    )


def get_category_rejection_message(category: str) -> str:
    """Return shopper-facing message when a garment category is restricted or blocked."""
    return (
        f"Virtual try-on is not currently available for this garment type ({category}). "
        "You can still view the product details and merchant listing."
    )
