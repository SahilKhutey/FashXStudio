from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID


@dataclass(frozen=True)
class RankingWeights:
    """Configurable weights for personalized discovery ranking.

    Default sum: 0.18 + 0.10 + 0.10 + 0.18 + 0.14 + 0.10 + 0.15 + 0.05 = 1.00.
    """

    style: float = 0.18
    occasion: float = 0.10
    color: float = 0.10
    size: float = 0.18
    budget: float = 0.14
    freshness: float = 0.10
    semantic: float = 0.15
    tryon: float = 0.05


def cosine_similarity(
    vec_a: Sequence[float] | None,
    vec_b: Sequence[float] | None,
) -> float | None:
    """Compute cosine similarity between two vectors.

    Returns None if either vector is None, lengths mismatch, contains non-finite values,
    or either vector has zero norm.
    """
    if vec_a is None or vec_b is None:
        return None
    if len(vec_a) != len(vec_b) or len(vec_a) == 0:
        return None

    dot = 0.0
    norm_a_sq = 0.0
    norm_b_sq = 0.0

    for a, b in zip(vec_a, vec_b, strict=True):
        if not math.isfinite(a) or not math.isfinite(b):
            return None
        dot += a * b
        norm_a_sq += a * a
        norm_b_sq += b * b

    if norm_a_sq < 1e-12 or norm_b_sq < 1e-12:
        return None

    denom = math.sqrt(norm_a_sq) * math.sqrt(norm_b_sq)
    sim = dot / denom
    # Bound to [-1.0, 1.0] to guard against precision float errors
    return max(-1.0, min(1.0, sim))


@dataclass
class ScoredGarmentCandidate:
    garment_id: UUID
    category: str
    subcategory: str | None
    brand_id: UUID | None
    brand_name: str
    price_minor: int
    dominant_color: str | None
    silhouette: str | None
    embedding: list[float] | None
    tryon_supported: bool
    style_score: float = 0.5
    occasion_score: float = 0.5
    color_score: float = 0.5
    size_score: float = 1.0
    budget_score: float = 1.0
    freshness_score: float = 0.5
    semantic_score: float | None = None
    final_score: float = 0.0
    reason_chips: list[str] = field(default_factory=list)
    stylist_explanation: str = ""
    extra: dict[str, Any] = field(default_factory=dict)


def score_candidate(
    candidate: ScoredGarmentCandidate,
    weights: RankingWeights = RankingWeights(),
) -> float:
    """Compute normalized composite score with dynamic reweighting for missing features.

    When semantic_score is None, the semantic weight is dynamically omitted from the denominator,
    so the final score is strictly re-normalized over available features without artificial fillers.
    """
    available_terms: list[tuple[float, float]] = [
        (weights.style, max(0.0, min(1.0, candidate.style_score))),
        (weights.occasion, max(0.0, min(1.0, candidate.occasion_score))),
        (weights.color, max(0.0, min(1.0, candidate.color_score))),
        (weights.size, max(0.0, min(1.0, candidate.size_score))),
        (weights.budget, max(0.0, min(1.0, candidate.budget_score))),
        (weights.freshness, max(0.0, min(1.0, candidate.freshness_score))),
        (weights.tryon, 1.0 if candidate.tryon_supported else 0.0),
    ]

    if candidate.semantic_score is not None:
        # Cosine similarity in [-1, 1] mapped to [0, 1] for relevance scoring
        sem_val = max(0.0, min(1.0, (candidate.semantic_score + 1.0) / 2.0))
        available_terms.append((weights.semantic, sem_val))

    total_weight = sum(w for w, _ in available_terms)
    if total_weight <= 0.0:
        return 0.5

    raw_score = sum(w * val for w, val in available_terms) / total_weight
    return round(max(0.0, min(1.0, raw_score)), 4)


def apply_mmr_diversification(
    items: list[ScoredGarmentCandidate],
    top_k: int = 20,
    diversity_lambda: float = 0.7,
    max_per_brand: int = 3,
    max_per_subcategory: int = 3,
) -> list[ScoredGarmentCandidate]:
    r"""Maximal Marginal Relevance (MMR) re-ranking with hard brand and subcategory caps.

    MMR = argmax_{d_i in R \ S} [ lambda * Sim1(d_i, q) - (1 - lambda) * max_{d_j in S} Sim2(d_i, d_j) ]
    """
    if not items:
        return []

    # Sort candidates by relevance score descending
    candidates = sorted(items, key=lambda x: x.final_score, reverse=True)
    selected: list[ScoredGarmentCandidate] = []
    brand_counts: dict[str, int] = {}
    subcat_counts: dict[str, int] = {}

    while candidates and len(selected) < top_k:
        best_candidate: ScoredGarmentCandidate | None = None
        best_index: int = -1
        best_mmr_score: float = -float("inf")

        for idx, cand in enumerate(candidates):
            b_key = cand.brand_name.strip().lower() if cand.brand_name else "unknown"
            s_key = (cand.subcategory or cand.category).strip().lower()

            # Enforce hard diversity caps
            if b_key != "unknown" and brand_counts.get(b_key, 0) >= max_per_brand:
                continue
            if subcat_counts.get(s_key, 0) >= max_per_subcategory:
                continue

            rel_score = cand.final_score

            # Similarity to already selected items
            if not selected:
                max_sim_to_selected = 0.0
            else:
                sims: list[float] = []
                for s in selected:
                    if cand.embedding and s.embedding:
                        cos = cosine_similarity(cand.embedding, s.embedding)
                        sim = max(0.0, cos) if cos is not None else 0.5
                    else:
                        # Category / color overlap proxy when embeddings not both present
                        cat_overlap = 0.6 if cand.category == s.category else 0.0
                        color_overlap = 0.4 if cand.dominant_color == s.dominant_color else 0.0
                        sim = cat_overlap + color_overlap
                    sims.append(sim)
                max_sim_to_selected = max(sims) if sims else 0.0

            mmr = diversity_lambda * rel_score - (1.0 - diversity_lambda) * max_sim_to_selected

            if mmr > best_mmr_score:
                best_mmr_score = mmr
                best_candidate = cand
                best_index = idx

        if best_candidate is None:
            # If all remaining exceed caps, pick the top remaining unselected candidate to satisfy top_k
            best_candidate = candidates[0]
            best_index = 0

        selected.append(best_candidate)
        b_key = best_candidate.brand_name.strip().lower() if best_candidate.brand_name else "unknown"
        s_key = (best_candidate.subcategory or best_candidate.category).strip().lower()
        brand_counts[b_key] = brand_counts.get(b_key, 0) + 1
        subcat_counts[s_key] = subcat_counts.get(s_key, 0) + 1
        candidates.pop(best_index)

    return selected
