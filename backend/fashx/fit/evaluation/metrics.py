"""Accuracy, coverage, abstention, and confidence calibration metrics (Phase 08.3 - Task 8.3.11)."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from fashx.fit.enums import EvaluationLabel, RecommendationStatus

CALIBRATION_BANDS: tuple[tuple[str, float, float], ...] = (
    ("0.50-0.59", 0.50, 0.599999),
    ("0.60-0.69", 0.60, 0.699999),
    ("0.70-0.79", 0.70, 0.799999),
    ("0.80-0.89", 0.80, 0.899999),
    ("0.90-1.00", 0.90, 1.000001),
)


@dataclass(frozen=True)
class EvaluationCase:
    """Evaluated prediction paired with its manually labelled expected outcome."""

    expected_size: str | None
    predicted_size: str | None
    expected_abstention: bool
    predicted_abstention: bool
    acceptable_sizes: tuple[str, ...] = ()
    expected_label: EvaluationLabel = EvaluationLabel.RECOMMENDED_SIZE
    predicted_status: RecommendationStatus = RecommendationStatus.RECOMMENDED
    category: str = "UNKNOWN"
    merchant_id: str = "UNKNOWN"
    confidence_score: float | None = None
    required_evidence_violated: bool = False
    unsupported_category_recommended: bool = False
    unauthorized_chart_used: bool = False
    stale_chart_recommended: bool = False


@dataclass(frozen=True)
class CalibrationBin:
    """Reliability bin mapping internal confidence band to observed accuracy."""

    band: str
    cases: int
    correct: int
    observed_accuracy: float


@dataclass(frozen=True)
class GroupMetrics:
    """Slice metrics computed independently per category or merchant."""

    key: str
    total_cases: int
    recommendations_made: int
    exact_size_accuracy: float | None
    acceptable_size_accuracy: float | None
    coverage: float
    abstention_rate: float
    false_recommendation_rate: float | None
    small_sample_warning: bool


@dataclass(frozen=True)
class EvaluationMetricsSummary:
    """Complete evaluation metric bundle across overall dataset, categories, merchants, and calibration."""

    total_cases: int
    recommendations_made: int
    abstentions_made: int
    coverage: float
    abstention_rate: float
    exact_size_accuracy: float | None
    acceptable_size_accuracy: float | None
    false_recommendation_rate: float | None
    no_match_detection_rate: float | None
    calibration_bins: tuple[CalibrationBin, ...]
    category_breakdown: dict[str, GroupMetrics] = field(default_factory=dict)
    merchant_breakdown: dict[str, GroupMetrics] = field(default_factory=dict)
    required_evidence_violations: int = 0
    unsupported_category_recommendations: int = 0
    unauthorized_chart_uses: int = 0
    stale_chart_recommendations: int = 0
    small_sample_warning: bool = False


def _is_exact_correct(c: EvaluationCase) -> bool:
    if c.predicted_abstention or c.expected_abstention:
        return False
    return c.predicted_size is not None and c.predicted_size == c.expected_size


def _is_acceptable_correct(c: EvaluationCase) -> bool:
    if c.predicted_abstention or c.expected_abstention or c.predicted_size is None:
        return False
    accepted = set(c.acceptable_sizes)
    if c.expected_size is not None:
        accepted.add(c.expected_size)
    return c.predicted_size in accepted


def _is_false_recommendation(c: EvaluationCase) -> bool:
    # A recommendation made when ground truth expected abstention / missing / unsupported / no-match
    if c.predicted_abstention:
        return False
    if c.expected_abstention:
        return True
    return c.expected_size is None and not c.acceptable_sizes


def _compute_group(key: str, cases: list[EvaluationCase]) -> GroupMetrics:
    total = len(cases)
    recs = [c for c in cases if not c.predicted_abstention]
    rec_count = len(recs)
    cov = round(rec_count / total, 4) if total else 0.0
    abst_rate = round((total - rec_count) / total, 4) if total else 0.0

    exact_acc = round(sum(_is_exact_correct(c) for c in recs) / rec_count, 4) if rec_count else None
    acc_acc = round(sum(_is_acceptable_correct(c) for c in recs) / rec_count, 4) if rec_count else None
    false_rate = round(sum(_is_false_recommendation(c) for c in recs) / rec_count, 4) if rec_count else None

    return GroupMetrics(
        key=key,
        total_cases=total,
        recommendations_made=rec_count,
        exact_size_accuracy=exact_acc,
        acceptable_size_accuracy=acc_acc,
        coverage=cov,
        abstention_rate=abst_rate,
        false_recommendation_rate=false_rate,
        small_sample_warning=total < 30,
    )


def evaluate_cases(cases: list[EvaluationCase]) -> dict[str, object]:
    """Compute core selective accuracy, coverage, calibration, and breakdown metrics."""
    if not cases:
        raise ValueError("Evaluation dataset is empty")

    total = len(cases)
    recommendations = [c for c in cases if not c.predicted_abstention]
    rec_count = len(recommendations)
    abst_count = total - rec_count

    exact_correct = sum(_is_exact_correct(c) for c in recommendations)
    acceptable_correct = sum(_is_acceptable_correct(c) for c in recommendations)
    false_recs = sum(_is_false_recommendation(c) for c in recommendations)

    no_match_cases = [c for c in cases if c.expected_label == EvaluationLabel.NO_MATCH]
    no_match_detected = sum(
        c.predicted_status == RecommendationStatus.NO_AVAILABLE_SIZE or c.predicted_abstention
        for c in no_match_cases
    )

    coverage = round(rec_count / total, 4)
    abstention_rate = round(abst_count / total, 4)
    selective_accuracy = round(exact_correct / rec_count, 4) if rec_count else None
    acceptable_accuracy = round(acceptable_correct / rec_count, 4) if rec_count else None
    false_recommendation_rate = round(false_recs / rec_count, 4) if rec_count else None
    no_match_rate = round(no_match_detected / len(no_match_cases), 4) if no_match_cases else None

    # Calibration across confidence bands (recommendations with non-null score)
    bins: list[CalibrationBin] = []
    for band_label, low, high in CALIBRATION_BANDS:
        in_bin = [
            c
            for c in recommendations
            if c.confidence_score is not None and low <= float(c.confidence_score) < high
        ]
        if in_bin:
            bin_correct = sum(_is_acceptable_correct(c) for c in in_bin)
            bins.append(
                CalibrationBin(
                    band=band_label,
                    cases=len(in_bin),
                    correct=bin_correct,
                    observed_accuracy=round(bin_correct / len(in_bin), 4),
                )
            )

    # Category and merchant slices
    by_cat: dict[str, list[EvaluationCase]] = {}
    by_merch: dict[str, list[EvaluationCase]] = {}
    for c in cases:
        by_cat.setdefault(c.category, []).append(c)
        by_merch.setdefault(c.merchant_id, []).append(c)

    cat_metrics = {k: _compute_group(k, v) for k, v in sorted(by_cat.items())}
    merch_metrics = {k: _compute_group(k, v) for k, v in sorted(by_merch.items())}

    req_violations = sum(1 for c in cases if c.required_evidence_violated)
    unsup_cat_recs = sum(1 for c in cases if c.unsupported_category_recommended)
    unauth_charts = sum(1 for c in cases if c.unauthorized_chart_used)
    stale_recs = sum(1 for c in cases if c.stale_chart_recommended)

    return {
        "total_cases": total,
        "recommendations_made": rec_count,
        "abstentions_made": abst_count,
        "coverage": coverage,
        "abstention_rate": abstention_rate,
        "selective_accuracy": selective_accuracy,
        "exact_size_accuracy": selective_accuracy,
        "acceptable_size_accuracy": acceptable_accuracy,
        "false_recommendation_rate": false_recommendation_rate,
        "no_match_detection_rate": no_match_rate,
        "calibration_bins": bins,
        "category_breakdown": cat_metrics,
        "merchant_breakdown": merch_metrics,
        "required_evidence_violations": req_violations,
        "unsupported_category_recommendations": unsup_cat_recs,
        "unauthorized_chart_uses": unauth_charts,
        "stale_chart_recommendations": stale_recs,
        "small_sample_warning": total < 30,
        "calibration_demonstrated": len(recommendations) >= 100 and len(bins) >= 3,
    }


def score_to_float(score: Decimal | float | None) -> float | None:
    return float(score) if score is not None else None
