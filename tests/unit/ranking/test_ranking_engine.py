"""Deterministic unit tests for Phase 08.4 Personalized Product Ranking."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from fashx.catalog.taxonomy.registry import TaxonomyCategoryNode, TaxonomyRegistry
from fashx.ranking.category import RegistryTaxonomyAdapter, category_score
from fashx.ranking.color import color_preference_score
from fashx.ranking.config import FeatureWeights
from fashx.ranking.contracts import (
    CandidateVariant,
    RankingCandidate,
    RankingContext,
    ShopperPreferenceSnapshot,
    SourcePermissionSnapshot,
)
from fashx.ranking.eligibility import evaluate_eligibility
from fashx.ranking.enums import AvailabilityStatus, RankingReasonCode, SizeAvailability
from fashx.ranking.feedback import explicit_feedback_score
from fashx.ranking.price import price_preference_score
from fashx.ranking.quality import combined_quality_score, merchant_quality_score
from fashx.ranking.scorer import FeatureValues, calculate_score
from fashx.ranking.service import PersonalizedRankingService
from fashx.ranking.size import check_size_availability
from fashx.ranking.style import style_preference_score
from fashx.ranking.visual_similarity import compute_visual_similarity, normalize_cosine_similarity


def _make_taxonomy() -> RegistryTaxonomyAdapter:
    nodes = {
        "tops": TaxonomyCategoryNode(
            id="tops",
            label="Tops",
            parent_id=None,
            path="tops",
            children_ids=["SHIRTS", "TSHIRTS"],
            is_leaf=False,
        ),
        "SHIRTS": TaxonomyCategoryNode(
            id="SHIRTS", label="Shirts", parent_id="tops", path="tops/SHIRTS"
        ),
        "TSHIRTS": TaxonomyCategoryNode(
            id="TSHIRTS", label="T-Shirts", parent_id="tops", path="tops/TSHIRTS"
        ),
        "FOOTWEAR": TaxonomyCategoryNode(
            id="FOOTWEAR", label="Footwear", parent_id=None, path="FOOTWEAR"
        ),
    }
    reg = TaxonomyRegistry(
        version="v1.0.0",
        categories=nodes,
        garment_types={},
        occasions={},
        audiences={},
        color_families={},
        color_shades={},
        patterns={},
        materials={},
        sleeves={},
        necklines={},
        collars={},
        fits={},
        silhouettes={},
        indian_wear={},
        western_wear={},
        footwear={},
        accessories={},
        missing_values={},
    )
    return RegistryTaxonomyAdapter(reg)


def _base_candidate(**overrides: object) -> RankingCandidate:
    defaults: dict[str, object] = {
        "product_id": "prod-1",
        "merchant_id": "merch-1",
        "merchant_offer_id": "offer-1",
        "title": "Oxford Casual Shirt",
        "category_id": "SHIRTS",
        "price": Decimal("1199"),
        "currency": "INR",
        "variants": (
            CandidateVariant(variant_id="v-m", size_label="M", stock_status="IN_STOCK"),
        ),
        "style_tags": {"CASUAL": 0.95, "MINIMAL": 0.90},
        "primary_colors": ("NAVY",),
        "image_quality": 0.9,
        "attribute_completeness": 0.9,
        "data_freshness": 0.95,
        "availability_verified_at": datetime.now(UTC),
    }
    defaults.update(overrides)
    return RankingCandidate(**defaults)  # type: ignore[arg-type]


def test_category_relevance_exact_related_unrelated_and_unknown() -> None:
    tax = _make_taxonomy()
    assert category_score("SHIRTS", "SHIRTS", tax) == 1.0
    assert category_score("SHIRTS", "TSHIRTS", tax) == 0.65
    assert category_score("SHIRTS", "FOOTWEAR", tax) == 0.0
    assert category_score(None, "FOOTWEAR", tax) == 1.0
    assert category_score("UNKNOWN_CAT", "SHIRTS", tax) == 0.0


def test_style_and_color_preferences_with_confidence_and_conflicts() -> None:
    assert (
        style_preference_score(
            {"MINIMAL": 0.9, "OVERSIZED": 0.4},
            liked_styles={"MINIMAL": 1.0},
            disliked_styles={"OVERSIZED": 0.9},
            min_confidence=0.70,
        )
        == 1.0
    )
    assert style_preference_score({"CASUAL": 0.9}, {}, {}) == 0.5
    assert color_preference_score(("NAVY",), {"NAVY"}, set()) == 1.0
    assert color_preference_score((), {"NAVY"}, set(), secondary_colors=("NAVY",)) == 0.75
    assert color_preference_score(("NAVY", "NEON_GREEN"), {"NAVY"}, {"NEON_GREEN"}) == 0.5
    assert (
        color_preference_score(
            ("NAVY",),
            {"NAVY"},
            set(),
            color_confidences={"NAVY": 0.3},
            min_confidence=0.7,
        )
        == 0.5
    )


def test_price_scoring_and_currency_mismatch_guard() -> None:
    mid_score = price_preference_score(Decimal("1000"), Decimal("500"), Decimal("1500"))
    edge_score = price_preference_score(Decimal("1199"), Decimal("500"), Decimal("1500"))
    assert mid_score == 1.0
    assert 0.85 < edge_score < 1.0
    assert price_preference_score(Decimal("2000"), Decimal("500"), Decimal("1500")) == 0.0
    assert price_preference_score(None, Decimal("500"), Decimal("1500")) == 0.0
    with pytest.raises(ValueError):
        price_preference_score(
            Decimal("100"),
            Decimal("50"),
            Decimal("200"),
            offer_currency="USD",
            target_currency="INR",
        )


def test_size_availability_and_eligibility_gates() -> None:
    variants = [
        CandidateVariant("v1", "M", "OUT_OF_STOCK", merchant_size_system="UK"),
        CandidateVariant("v2", "L", "IN_STOCK", merchant_size_system="UK"),
    ]
    assert check_size_availability(None, variants) == SizeAvailability.NOT_APPLICABLE
    assert check_size_availability("M", variants) == SizeAvailability.UNAVAILABLE
    assert check_size_availability("L", variants) == SizeAvailability.AVAILABLE
    assert check_size_availability("XL", variants) == SizeAvailability.UNKNOWN
    assert (
        check_size_availability("L", variants, required_size_system="US")
        == SizeAvailability.UNKNOWN
    )

    takedown = _base_candidate(is_taken_down=True)
    ctx = RankingContext(category_id="SHIRTS", selected_size="M", require_selected_size=True)
    res_td = evaluate_eligibility(takedown, ctx)
    assert res_td.eligible is False
    assert "PRODUCT_TAKEN_DOWN" in res_td.reason_codes

    oos = _base_candidate(availability_status=AvailabilityStatus.OUT_OF_STOCK.value)
    assert evaluate_eligibility(oos, ctx).eligible is False

    stale = _base_candidate(availability_verified_at=datetime.now(UTC) - timedelta(days=5))
    assert evaluate_eligibility(stale, ctx, max_age_seconds=3600).eligible is False

    unpermitted = _base_candidate(
        permissions=SourcePermissionSnapshot(can_display_product=False)
    )
    assert evaluate_eligibility(unpermitted, ctx).eligible is False


def test_visual_similarity_and_feedback_and_quality_guards() -> None:
    assert normalize_cosine_similarity(0.5, 0.0, 1.0) == 0.5
    with pytest.raises(ValueError):
        normalize_cosine_similarity(0.5, 1.0, 1.0)

    sim = compute_visual_similarity(
        (1.0, 0.0),
        (1.0, 0.0),
        reference_model="clip",
        candidate_model="clip",
        reference_version="v1",
        candidate_version="v1",
    )
    assert sim == 1.0

    with pytest.raises(ValueError):
        compute_visual_similarity(
            (1.0, 0.0),
            (1.0, 0.0),
            reference_model="clip",
            candidate_model="other",
            reference_version="v1",
            candidate_version="v1",
        )

    assert explicit_feedback_score(["VIEW"]) == 0.5
    assert explicit_feedback_score(["LIKE"]) == 1.0
    assert explicit_feedback_score(["DISLIKE"]) == 0.0
    assert explicit_feedback_score(["LIKE", "DISLIKE"]) == 0.0
    assert merchant_quality_score(None, None, None, is_new_merchant=True) == 0.5
    assert combined_quality_score(_base_candidate(is_sponsored=True)) == combined_quality_score(
        _base_candidate(is_sponsored=False)
    )


def test_scorer_normalizes_missing_features_and_rejects_invalid_inputs() -> None:
    all_max = FeatureValues(1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0)
    assert calculate_score(all_max).score == 100.0

    no_visual = FeatureValues(1.0, 1.0, 1.0, 1.0, 1.0, 1.0, None, 1.0, 1.0)
    res = calculate_score(no_visual)
    assert res.score == 100.0
    assert "visual" not in res.contributions

    with pytest.raises(ValueError):
        calculate_score(FeatureValues(1.5, 1.0, 1.0, 1.0, 1.0, 1.0, None, 1.0, 1.0))

    with pytest.raises(ValueError):
        calculate_score(all_max, FeatureWeights(category=-0.1))

    with pytest.raises(ValueError):
        calculate_score(FeatureValues(None, None, None, None, None, None, None, None, None))


def test_service_determinism_explanations_and_cache_invalidation() -> None:
    tax = _make_taxonomy()
    svc = PersonalizedRankingService(taxonomy=tax)
    shopper = ShopperPreferenceSnapshot(
        shopper_id="user-1",
        profile_revision=1,
        liked_styles={"MINIMAL": 1.0, "CASUAL": 0.8},
        disliked_styles={"OVERSIZED": 0.9},
        preferred_colors=frozenset({"NAVY", "OLIVE"}),
        budget_min=Decimal("500"),
        budget_max=Decimal("1500"),
    )
    strong = _base_candidate(product_id="p-strong", primary_colors=("NAVY",))
    weak = _base_candidate(
        product_id="p-weak",
        style_tags={"OVERSIZED": 0.95},
        primary_colors=("WHITE",),
        variants=(CandidateVariant("v-l", "L", "IN_STOCK"),),
    )
    taken_down = _base_candidate(product_id="p-td", is_taken_down=True)

    ctx = RankingContext(query="casual shirts", category_id="SHIRTS", selected_size="M")
    first = svc.rank(shopper_profile=shopper, candidates=[weak, taken_down, strong], context=ctx)
    second = svc.rank(shopper_profile=shopper, candidates=[weak, taken_down, strong], context=ctx)

    assert [r.product_id for r in first.results] == ["p-strong", "p-weak"]
    assert first.cache_hit is False
    assert second.cache_hit is True
    assert [r.product_id for r in second.results] == [r.product_id for r in first.results]
    assert RankingReasonCode.SIZE_AVAILABLE in first.results[0].reasons
    assert RankingReasonCode.SIZE_AVAILABLE not in first.results[1].reasons
