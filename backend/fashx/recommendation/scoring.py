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
    taste_similarity: float
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
    """Compute normalized relevance score and grounded, non-hallucinated reason chips."""
    # 1. Taste similarity
    taste_sim = 0.5  # Neutral default when no taste vector available
    if has_taste_signal and taste_vector is not None:
        emb = item.embedding
        if not emb:
            emb = fallback_text_embedding(item.title, item.category, item.subcategory)
        taste_sim = float(cosine_similarity(taste_vector, emb))
        # Bound to [0.0, 1.0]
        taste_sim = max(0.0, min(1.0, taste_sim))

    # 2. Compatibility score from compatibility matrix
    compat_score = max(0.0, min(1.0, compatibility.total_score))
    color_score = max(0.0, min(1.0, compatibility.color_score))
    silhouette_score = max(0.0, min(1.0, compatibility.silhouette_score))

    # 3. Weighted relevance score
    if has_taste_signal and taste_vector is not None:
        total_weight = weight_taste + weight_compat
        w_taste = weight_taste / total_weight
        w_compat = weight_compat / total_weight
        relevance = round(w_taste * taste_sim + w_compat * compat_score, 3)
    else:
        relevance = round(compat_score, 3)

    relevance = max(0.0, min(1.0, relevance))

    # 4. Feature contributions
    feature_contributions = {
        "taste_similarity": round(taste_sim * (weight_taste if has_taste_signal else 0.0), 3),
        "compatibility": round(compat_score * (weight_compat if has_taste_signal else 1.0), 3),
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
    if has_taste_signal and taste_sim >= 0.70:
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
