from __future__ import annotations

import math
import uuid

from fashx.discovery.scoring import (
    ScoredGarmentCandidate,
    apply_mmr_diversification,
    score_candidate,
)


def compute_dcg(relevances: list[float], k: int) -> float:
    return sum((2.0**rel - 1.0) / math.log2(i + 2.0) for i, rel in enumerate(relevances[:k]))


def compute_ndcg(relevances: list[float], ideal_relevances: list[float], k: int) -> float:
    dcg = compute_dcg(relevances, k)
    idcg = compute_dcg(sorted(ideal_relevances, reverse=True), k)
    if idcg <= 0.0:
        return 0.0
    return dcg / idcg


def test_ranking_ndcg_and_precision_metrics() -> None:
    # 20 catalog candidates with ground-truth user affinity
    candidates: list[ScoredGarmentCandidate] = []
    ground_truth_relevant_ids: set[uuid.UUID] = set()

    for i in range(20):
        gid = uuid.uuid4()
        is_relevant = i < 8  # Top 8 items are truly relevant to user
        if is_relevant:
            ground_truth_relevant_ids.add(gid)

        cand = ScoredGarmentCandidate(
            garment_id=gid,
            category="tops",
            subcategory="shirt",
            brand_id=None,
            brand_name=f"Brand_{i % 5}",
            price_minor=2000 + i * 200,
            dominant_color="navy" if is_relevant else "lime",
            silhouette="slim" if is_relevant else "oversized",
            embedding=None,
            tryon_supported=True,
            style_score=0.95 if is_relevant else 0.30,
            color_score=0.90 if is_relevant else 0.20,
            size_score=1.00,
            budget_score=1.00,
            freshness_score=0.70,
            semantic_score=None,
        )
        cand.final_score = score_candidate(cand)
        candidates.append(cand)

    # Rank with MMR
    ranked = apply_mmr_diversification(candidates, top_k=5, diversity_lambda=0.8)
    assert len(ranked) == 5

    # 1. Hard Constraint Violation Rate must be 0%
    budget_limit = 5000
    violations = sum(1 for c in ranked if c.price_minor > budget_limit)
    violation_rate = violations / len(ranked)
    assert violation_rate == 0.0, f"Constraint violation rate must be 0.0, got {violation_rate}"

    # 2. Precision@5
    hits = sum(1 for c in ranked if c.garment_id in ground_truth_relevant_ids)
    precision_at_5 = hits / 5.0
    assert precision_at_5 >= 0.80, f"Precision@5 must be >= 0.80, got {precision_at_5}"

    # 3. Recall@5
    recall_at_5 = hits / len(ground_truth_relevant_ids)
    assert recall_at_5 >= 0.50, f"Recall@5 must be >= 0.50, got {recall_at_5}"

    # 4. NDCG@5
    actual_rels = [1.0 if c.garment_id in ground_truth_relevant_ids else 0.0 for c in ranked]
    ideal_rels = [1.0] * len(ground_truth_relevant_ids) + [0.0] * (20 - len(ground_truth_relevant_ids))
    ndcg_5 = compute_ndcg(actual_rels, ideal_rels, k=5)
    assert ndcg_5 >= 0.85, f"NDCG@5 must be >= 0.85, got {ndcg_5}"
