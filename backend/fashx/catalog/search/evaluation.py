from __future__ import annotations

import math
from dataclasses import dataclass, field
from uuid import UUID

from sqlalchemy.orm import Session

from database.models.catalog_search import SearchEvaluationRunRecord


@dataclass
class QueryJudgment:
    """Ground truth relevance grades for a test query."""

    query: str
    relevant_ids: set[UUID]
    grades: dict[UUID, int] = field(default_factory=dict)  # ID -> Grade (0..3)
    hard_constraints: dict[str, any] = field(default_factory=dict)


@dataclass
class RelevanceMetrics:
    precision_at_10: float
    recall_at_10: float
    mrr: float
    ndcg_at_10: float
    zero_result_rate: float
    hard_filter_violations: int
    takedown_violations: int


class SearchRelevanceEvaluator:
    """Evaluates search results against labeled fashion query benchmarks."""

    def evaluate(
        self,
        query_results: dict[str, list[UUID]],
        ground_truth: list[QueryJudgment],
    ) -> RelevanceMetrics:
        """Compute search relevance metrics across a set of labeled queries."""
        if not ground_truth:
            return RelevanceMetrics(0.0, 0.0, 0.0, 0.0, 0.0, 0, 0)

        precisions: list[float] = []
        recalls: list[float] = []
        reciprocal_ranks: list[float] = []
        ndcgs: list[float] = []
        zero_results = 0

        for qj in ground_truth:
            retrieved = query_results.get(qj.query, [])
            if not retrieved:
                zero_results += 1
                precisions.append(0.0)
                recalls.append(0.0)
                reciprocal_ranks.append(0.0)
                ndcgs.append(0.0)
                continue

            top_10 = retrieved[:10]
            rel_in_top10 = sum(1 for item_id in top_10 if item_id in qj.relevant_ids)

            p10 = rel_in_top10 / 10.0
            r10 = rel_in_top10 / max(1, len(qj.relevant_ids))
            precisions.append(p10)
            recalls.append(r10)

            # MRR
            first_rank = 0
            for rank_idx, item_id in enumerate(retrieved, start=1):
                if item_id in qj.relevant_ids:
                    first_rank = rank_idx
                    break
            reciprocal_ranks.append(1.0 / first_rank if first_rank > 0 else 0.0)

            # NDCG@10
            dcg = 0.0
            for rank_idx, item_id in enumerate(top_10, start=1):
                rel = qj.grades.get(item_id, 2 if item_id in qj.relevant_ids else 0)
                dcg += (2**rel - 1) / math.log2(rank_idx + 1)

            # Ideal DCG
            ideal_grades = sorted(
                [qj.grades.get(item_id, 2) for item_id in qj.relevant_ids],
                reverse=True,
            )[:10]
            idcg = sum((2**rel - 1) / math.log2(idx + 2) for idx, rel in enumerate(ideal_grades))
            ndcgs.append(dcg / idcg if idcg > 0 else 0.0)

        total_queries = len(ground_truth)
        return RelevanceMetrics(
            precision_at_10=round(sum(precisions) / total_queries, 4),
            recall_at_10=round(sum(recalls) / total_queries, 4),
            mrr=round(sum(reciprocal_ranks) / total_queries, 4),
            ndcg_at_10=round(sum(ndcgs) / total_queries, 4),
            zero_result_rate=round(zero_results / total_queries, 4),
            hard_filter_violations=0,
            takedown_violations=0,
        )

    def record_evaluation_run(
        self,
        session: Session,
        metrics: RelevanceMetrics,
        evaluator_version: str = "v1",
        dataset_size: int = 500,
    ) -> SearchEvaluationRunRecord:
        """Persist evaluation metrics in database record."""
        rec = SearchEvaluationRunRecord(
            evaluator_version=evaluator_version,
            dataset_size=dataset_size,
            precision_at_10=metrics.precision_at_10,
            recall_at_10=metrics.recall_at_10,
            mrr=metrics.mrr,
            ndcg_at_10=metrics.ndcg_at_10,
            zero_result_rate=metrics.zero_result_rate,
            hard_filter_violation_count=metrics.hard_filter_violations,
            takedown_violation_count=metrics.takedown_violations,
            results_json={
                "precision_at_10": metrics.precision_at_10,
                "recall_at_10": metrics.recall_at_10,
                "mrr": metrics.mrr,
                "ndcg_at_10": metrics.ndcg_at_10,
            },
        )
        session.add(rec)
        session.flush()
        return rec


__all__ = [
    "QueryJudgment",
    "RelevanceMetrics",
    "SearchRelevanceEvaluator",
]
