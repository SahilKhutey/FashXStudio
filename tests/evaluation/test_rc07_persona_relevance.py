from __future__ import annotations

import uuid

from fashx.discovery.scoring import (
    ScoredGarmentCandidate,
    score_candidate,
)


def make_catalog_pool() -> list[dict]:
    return [
        {
            "id": uuid.uuid4(),
            "title": "Navy Wool Blazer",
            "category": "blazers",
            "dominant_color": "navy",
            "formality": "formal",
            "silhouette": "slim",
            "price_minor": 8500,
        },
        {
            "id": uuid.uuid4(),
            "title": "Black Formal Trousers",
            "category": "trousers",
            "dominant_color": "black",
            "formality": "formal",
            "silhouette": "slim",
            "price_minor": 4500,
        },
        {
            "id": uuid.uuid4(),
            "title": "Olive Linen Overshirt",
            "category": "shirts",
            "dominant_color": "olive",
            "formality": "casual",
            "silhouette": "regular",
            "price_minor": 3200,
        },
        {
            "id": uuid.uuid4(),
            "title": "Beige Cotton Chinos",
            "category": "pants",
            "dominant_color": "beige",
            "formality": "casual",
            "silhouette": "regular",
            "price_minor": 2800,
        },
        {
            "id": uuid.uuid4(),
            "title": "Maroon Silk Kurta Set",
            "category": "ethnic",
            "dominant_color": "maroon",
            "formality": "festive",
            "silhouette": "straight",
            "price_minor": 6500,
        },
    ]


def test_persona_relevance_divergence() -> None:
    pool = make_catalog_pool()

    # Persona A: Formal Navy Professional
    scored_a: list[tuple[dict, float]] = []
    for item in pool:
        style_sc = 0.95 if item["formality"] == "formal" else 0.20
        color_sc = 0.95 if item["dominant_color"] in ("navy", "black") else 0.30
        sil_sc = 0.90 if item["silhouette"] == "slim" else 0.40
        cand = ScoredGarmentCandidate(
            garment_id=item["id"],
            category=item["category"],
            subcategory=None,
            brand_id=None,
            brand_name="Brand",
            price_minor=item["price_minor"],
            dominant_color=item["dominant_color"],
            silhouette=item["silhouette"],
            embedding=None,
            tryon_supported=True,
            style_score=style_sc,
            color_score=color_sc,
            size_score=sil_sc,
        )
        cand.final_score = score_candidate(cand)
        scored_a.append((item, cand.final_score))

    top_a = sorted(scored_a, key=lambda x: x[1], reverse=True)[0][0]
    assert top_a["title"] in ("Navy Wool Blazer", "Black Formal Trousers")

    # Persona B: Casual Earth-Tone Enthusiast
    scored_b: list[tuple[dict, float]] = []
    for item in pool:
        style_sc = 0.95 if item["formality"] == "casual" else 0.20
        color_sc = 0.95 if item["dominant_color"] in ("olive", "beige") else 0.30
        sil_sc = 0.90 if item["silhouette"] == "regular" else 0.40
        cand = ScoredGarmentCandidate(
            garment_id=item["id"],
            category=item["category"],
            subcategory=None,
            brand_id=None,
            brand_name="Brand",
            price_minor=item["price_minor"],
            dominant_color=item["dominant_color"],
            silhouette=item["silhouette"],
            embedding=None,
            tryon_supported=True,
            style_score=style_sc,
            color_score=color_sc,
            size_score=sil_sc,
        )
        cand.final_score = score_candidate(cand)
        scored_b.append((item, cand.final_score))

    top_b = sorted(scored_b, key=lambda x: x[1], reverse=True)[0][0]
    assert top_b["title"] in ("Olive Linen Overshirt", "Beige Cotton Chinos")

    # Verify distinct top picks across personas (zero cross-contamination)
    assert top_a["id"] != top_b["id"]
