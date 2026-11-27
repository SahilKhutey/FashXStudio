"""Offline comparison report for baseline vs. personalized ranking (Task 8.4.14)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from fashx.ranking.category import TaxonomyInterface
from fashx.ranking.evaluation.comparison import (
    SystemEvaluationSummary,
    evaluate_ranking_version,
)
from fashx.ranking.evaluation.dataset import JudgedQueryPair


@dataclass(frozen=True)
class RankingComparisonReport:
    """Reproducible baseline-vs-personalized evaluation report."""

    dataset_version: str
    taxonomy_version: str
    generated_at: datetime
    baseline: SystemEvaluationSummary
    personalized: SystemEvaluationSummary
    ndcg_lift: float
    safety_gates_passed: bool


def build_ranking_comparison_report(
    *,
    dataset_version: str,
    dataset: list[JudgedQueryPair],
    taxonomy: TaxonomyInterface,
    baseline_version: str = "baseline-v1",
    personalized_version: str = "personalized-v1",
) -> RankingComparisonReport:
    """Evaluate baseline and personalized ranking on the exact same dataset."""
    baseline = evaluate_ranking_version(
        dataset=dataset,
        taxonomy=taxonomy,
        ranking_version=baseline_version,
    )
    personalized = evaluate_ranking_version(
        dataset=dataset,
        taxonomy=taxonomy,
        ranking_version=personalized_version,
    )
    lift = round(personalized.ndcg_at_10 - baseline.ndcg_at_10, 4)
    safety_ok = (
        personalized.takedown_leakage_count == 0
        and personalized.out_of_stock_leakage_count == 0
        and personalized.size_violation_count == 0
    )
    return RankingComparisonReport(
        dataset_version=dataset_version,
        taxonomy_version=taxonomy.version,
        generated_at=datetime.now(UTC),
        baseline=baseline,
        personalized=personalized,
        ndcg_lift=lift,
        safety_gates_passed=safety_ok,
    )
