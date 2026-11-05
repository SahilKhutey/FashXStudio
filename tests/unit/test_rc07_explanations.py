from __future__ import annotations

import uuid

from fashx.discovery.explanations import (
    build_grounded_reason_chips,
    build_grounded_stylist_explanation,
)
from fashx.discovery.scoring import ScoredGarmentCandidate


def test_grounded_reason_chips_derived_strictly_from_attributes() -> None:
    cand = ScoredGarmentCandidate(
        garment_id=uuid.uuid4(),
        category="tops",
        subcategory="kurta",
        brand_id=None,
        brand_name="FabIndia",
        price_minor=3500,
        dominant_color="olive",
        silhouette="straight",
        embedding=None,
        tryon_supported=True,
        style_score=0.90,
        color_score=0.88,
        size_score=1.00,
        budget_score=0.95,
        final_score=0.89,
        semantic_score=0.72,
    )

    chips = build_grounded_reason_chips(cand, user_styles=["casual", "traditional"])

    # Must contain grounded chips
    assert "Top Pick" in chips
    assert "Visual Taste Match" in chips or "Style Match" in chips
    assert len(chips) <= 3

    # Verifies no unverified fit hallucination chips
    for chip in chips:
        assert "exact fit" not in chip.lower()
        assert "guaranteed" not in chip.lower()


def test_grounded_stylist_explanation_no_hallucinated_measurements() -> None:
    cand = ScoredGarmentCandidate(
        garment_id=uuid.uuid4(),
        category="dresses",
        subcategory="midi",
        brand_id=None,
        brand_name="Zara",
        price_minor=4990,
        dominant_color="navy",
        silhouette="a_line",
        embedding=None,
        tryon_supported=True,
        style_score=0.85,
        color_score=0.80,
    )

    expl = build_grounded_stylist_explanation(cand, user_styles=["minimalist"])
    assert "minimalist" in expl
    assert "navy" in expl
    assert "try-on" in expl

    # Must not contain unmeasured waist/chest claims
    assert "chest" not in expl.lower()
    assert "waist" not in expl.lower()
