"""Explainable scoring engine for personalized garment discovery (Roadmap Step 3.2 / MVP 3).

Provides pure, testable scoring functions, feature attribution, grounded reason chips,
and fallback handling when embeddings are missing.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from fashx.catalog.embeddings.fake import FakeEmbedder
from fashx.recommendation.compatibility import CompatibilityScore
from fashx.recommendation.filters import CandidateItem
from fashx.recommendation.ranker import cosine_similarity


@dataclass(frozen=True)
class ScoringBreakdown:
    relevance_score: float
    taste_similarity: float | None
    compatibility_score: float
    color_score: float
    silhouette_score: float
    reason_chips: list[str] = field(default_factory=list)
    feature_contributions: dict[str, float] = field(default_factory=dict)


def fallback_text_embedding(
    title: str, category: str, subcategory: str | None = None
) -> list[float]:
    """Fallback text embedder when garment pre-computed embedding is missing."""
    text = f"{title} {category} {subcategory or ''}".strip()
    embedder = FakeEmbedder()
    return embedder.embed_text([text])[0]


def compute_explainable_score(
    item: CandidateItem,
    compatibility: CompatibilityScore,
    taste_vector: list[float] | None,
    has_taste_signal: bool = False,
    weight_taste: float = 0.5,
    weight_compat: float = 0.5,
) -> ScoringBreakdown:
    """Compute normalized relevance score and grounded, non-hallucinated reason chips with dynamic reweighting."""
    # 1. Taste similarity - missing vectors are represented as None rather than neutral 0.5
    taste_sim: float | None = None
    if has_taste_signal and taste_vector is not None:
        emb = item.embedding
        if not emb:
            emb = fallback_text_embedding(item.title, item.category, item.subcategory)
        raw_sim = cosine_similarity(taste_vector, emb)
        if raw_sim is not None:
            # Bound cosine similarity to [0.0, 1.0] for relevance scoring
            taste_sim = max(0.0, min(1.0, raw_sim))

    # 2. Compatibility score from compatibility matrix
    compat_score = max(0.0, min(1.0, compatibility.total_score))
    color_score = max(0.0, min(1.0, compatibility.color_score))
    silhouette_score = max(0.0, min(1.0, compatibility.silhouette_score))

    # 3. Dynamic weighted relevance score
    # S(u,g) = sum_{j in A} w_j s_j / sum_{j in A} w_j
    available_weights: list[tuple[float, float]] = [(weight_compat, compat_score)]
    if taste_sim is not None:
        available_weights.append((weight_taste, taste_sim))

    total_weight = sum(w for w, _ in available_weights)
    if total_weight > 0.0:
        relevance = sum(w * s for w, s in available_weights) / total_weight
    else:
        relevance = 0.5

    relevance = round(max(0.0, min(1.0, relevance)), 3)

    # 4. Feature contributions
    feature_contributions = {
        "taste_similarity": (
            round(taste_sim * (weight_taste / total_weight), 3)
            if taste_sim is not None
            else 0.0
        ),
        "compatibility": round(compat_score * (weight_compat / total_weight), 3),
        "color_harmony": round(color_score, 3),
        "silhouette_fit": round(silhouette_score, 3),
    }

    # 5. Grounded reason chips (strictly derived from validated conditions)
    chips: list[str] = []
    if relevance >= 0.85:
        chips.append("Top Pick")
    if color_score >= 0.85 and item.dominant_color:
        chips.append(f"{item.dominant_color.capitalize()} Harmony")
    elif silhouette_score >= 0.85 and item.silhouette:
        chips.append(f"{item.silhouette.replace('_', ' ').capitalize()} Cut")
    if taste_sim is not None and taste_sim >= 0.70:
        chips.append("Style Match")

    if not chips:
        if item.category:
            chips.append(item.category.capitalize())
        if item.dominant_color:
            chips.append(item.dominant_color.capitalize())

    return ScoringBreakdown(
        relevance_score=relevance,
        taste_similarity=taste_sim,
        compatibility_score=compat_score,
        color_score=color_score,
        silhouette_score=silhouette_score,
        reason_chips=chips[:3],
        feature_contributions=feature_contributions,
    )
