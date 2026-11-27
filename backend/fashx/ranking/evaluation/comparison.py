"""Baseline vs. personalized ranking comparison harness (Task 8.4.14)."""

from __future__ import annotations

from dataclasses import dataclass

from fashx.ranking.category import TaxonomyInterface
from fashx.ranking.enums import AvailabilityStatus
from fashx.ranking.evaluation.dataset import JudgedQueryPair
from fashx.ranking.evaluation.metrics import (
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
    reciprocal_rank,
)
from fashx.ranking.service import PersonalizedRankingService


@dataclass(frozen=True)
class SystemEvaluationSummary:
    """Aggregated offline ranking and safety metrics for one ranking version."""

    ranking_version: str
    query_count: int
    ndcg_at_10: float
    precision_at_10: float
    recall_at_10: float
    mrr: float
    dislike_suppression_rate: float
    size_violation_count: int
    out_of_stock_leakage_count: int
    takedown_leakage_count: int


def evaluate_ranking_version(
    *,
    dataset: list[JudgedQueryPair],
    taxonomy: TaxonomyInterface,
    ranking_version: str,
    k: int = 10,
) -> SystemEvaluationSummary:
    """Evaluate a ranking version on a held-out judged query dataset."""
    if not dataset:
        return SystemEvaluationSummary(
            ranking_version=ranking_version,
            query_count=0,
            ndcg_at_10=0.0,
            precision_at_10=0.0,
            recall_at_10=0.0,
            mrr=0.0,
            dislike_suppression_rate=1.0,
            size_violation_count=0,
            out_of_stock_leakage_count=0,
            takedown_leakage_count=0,
        )

    service = PersonalizedRankingService(taxonomy=taxonomy)
    ndcgs: list[float] = []
    precs: list[float] = []
    recalls: list[float] = []
    mrrs: list[float] = []
    disliked_total = 0
    disliked_suppressed = 0
    size_violations = 0
    oos_leakage = 0
    takedown_leakage = 0

    for pair in dataset:
        resp = service.rank(
            shopper_profile=pair.shopper_profile,
            candidates=list(pair.candidates),
            context=pair.context,
            ranking_version=ranking_version,
            use_cache=False,
        )
        ranked_rels = [pair.relevance_grades.get(item.product_id, 0) for item in resp.results]
        ideal_rels = list(pair.relevance_grades.values())
        total_rel = sum(1 for v in ideal_rels if v >= 2)

        ndcgs.append(ndcg_at_k(ranked_rels, ideal_rels, k))
        precs.append(precision_at_k(ranked_rels, k))
        recalls.append(recall_at_k(ranked_rels, total_rel, k))
        mrrs.append(reciprocal_rank(ranked_rels))

        top_ids = {item.product_id for item in resp.results[:k]}
        for disliked_id in pair.disliked_product_ids:
            disliked_total += 1
            if disliked_id not in top_ids or (
                resp.results and resp.results[0].product_id != disliked_id
            ):
                disliked_suppressed += 1

        by_id = {c.product_id: c for c in pair.candidates}
        for item in resp.results:
            cand = by_id.get(item.product_id)
            if cand is None:
                continue
            if cand.is_taken_down:
                takedown_leakage += 1
            if cand.availability_status != AvailabilityStatus.IN_STOCK.value:
                oos_leakage += 1
            if pair.context.selected_size and pair.context.require_selected_size:
                if not item.selected_size_available:
                    size_violations += 1

    n = len(dataset)
    return SystemEvaluationSummary(
        ranking_version=ranking_version,
        query_count=n,
        ndcg_at_10=round(sum(ndcgs) / n, 4),
        precision_at_10=round(sum(precs) / n, 4),
        recall_at_10=round(sum(recalls) / n, 4),
        mrr=round(sum(mrrs) / n, 4),
        dislike_suppression_rate=(
            round(disliked_suppressed / disliked_total, 4) if disliked_total else 1.0
        ),
        size_violation_count=size_violations,
        out_of_stock_leakage_count=oos_leakage,
        takedown_leakage_count=takedown_leakage,
    )
