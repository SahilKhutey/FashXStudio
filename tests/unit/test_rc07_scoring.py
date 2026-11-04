from __future__ import annotations

import uuid

from fashx.discovery.scoring import (
    RankingWeights,
    ScoredGarmentCandidate,
    apply_mmr_diversification,
    cosine_similarity,
    score_candidate,
)


def test_ranking_weights_sum_to_one() -> None:
    w = RankingWeights()
    total = (
        w.style
        + w.occasion
        + w.color
        + w.size
        + w.budget
        + w.freshness
        + w.semantic
        + w.tryon
    )
    assert abs(total - 1.00) < 1e-5


def test_cosine_similarity_edge_cases() -> None:
    v1 = [1.0, 0.0, 0.0]
    v2 = [1.0, 0.0, 0.0]
    v_orth = [0.0, 1.0, 0.0]
    v_opp = [-1.0, 0.0, 0.0]

    assert abs(cosine_similarity(v1, v2) - 1.0) < 1e-4
    assert abs(cosine_similarity(v1, v_orth) - 0.0) < 1e-4
    assert abs(cosine_similarity(v1, v_opp) - (-1.0)) < 1e-4

    # None / length mismatch / non-finite / zero norm
    assert cosine_similarity(None, v1) is None
    assert cosine_similarity(v1, None) is None
    assert cosine_similarity([1.0, 2.0], [1.0, 2.0, 3.0]) is None
    assert cosine_similarity([float("nan"), 0.0], [1.0, 0.0]) is None
    assert cosine_similarity([0.0, 0.0], [1.0, 0.0]) is None


def test_dynamic_reweighting_when_semantic_missing() -> None:
    cand_with_semantic = ScoredGarmentCandidate(
        garment_id=uuid.uuid4(),
        category="tops",
        subcategory="shirt",
        brand_id=None,
        brand_name="Brand A",
        price_minor=3000,
        dominant_color="navy",
        silhouette="slim",
        embedding=[0.1] * 512,
        tryon_supported=True,
        style_score=1.0,
        occasion_score=1.0,
        color_score=1.0,
        size_score=1.0,
        budget_score=1.0,
        freshness_score=1.0,
        semantic_score=1.0,  # maps to 1.0
    )
    score_all = score_candidate(cand_with_semantic)
    assert abs(score_all - 1.0) < 1e-4

    # Missing semantic score
    cand_no_semantic = ScoredGarmentCandidate(
        garment_id=uuid.uuid4(),
        category="tops",
        subcategory="shirt",
        brand_id=None,
        brand_name="Brand A",
        price_minor=3000,
        dominant_color="navy",
        silhouette="slim",
        embedding=None,
        tryon_supported=True,
        style_score=1.0,
        occasion_score=1.0,
        color_score=1.0,
        size_score=1.0,
        budget_score=1.0,
        freshness_score=1.0,
        semantic_score=None,  # Missing!
    )
    score_no_sem = score_candidate(cand_no_semantic)
    # Since all other available components are 1.0, dynamic reweighting yields 1.0
    assert abs(score_no_sem - 1.0) < 1e-4


def test_mmr_diversification_caps() -> None:
    # 5 items of Brand X, 2 items of Brand Y
    items: list[ScoredGarmentCandidate] = []
    for i in range(5):
        cand = ScoredGarmentCandidate(
            garment_id=uuid.uuid4(),
            category="tops",
            subcategory=f"sub_{i}",
            brand_id=None,
            brand_name="BrandX",
            price_minor=2000,
            dominant_color="blue",
            silhouette="regular",
            embedding=None,
            tryon_supported=True,
            final_score=0.95 - (i * 0.01),
        )
        items.append(cand)

    for i in range(3):
        cand = ScoredGarmentCandidate(
            garment_id=uuid.uuid4(),
            category="tops",
            subcategory=f"sub_y_{i}",
            brand_id=None,
            brand_name="BrandY",
            price_minor=2500,
            dominant_color="black",
            silhouette="regular",
            embedding=None,
            tryon_supported=True,
            final_score=0.85 - (i * 0.01),
        )
        items.append(cand)

    selected = apply_mmr_diversification(
        items,
        top_k=6,
        diversity_lambda=0.7,
        max_per_brand=3,
        max_per_subcategory=2,
    )
    assert len(selected) == 6

    # BrandX should have at most 3 items in the top results
    brand_x_count = sum(1 for c in selected if c.brand_name == "BrandX")
    brand_y_count = sum(1 for c in selected if c.brand_name == "BrandY")
    assert brand_x_count <= 3
    assert brand_y_count == 3
