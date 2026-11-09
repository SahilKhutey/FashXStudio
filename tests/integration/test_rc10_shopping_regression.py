"""RC10 shopping regression and catalog quality integration test."""
from __future__ import annotations

from datetime import UTC, datetime

from scripts.rc10.beta_gates import evaluate_beta_gates
from scripts.rc10.evaluate_catalog import evaluate_product
from scripts.rc10.evaluate_recommendations import ndcg_at_k, precision_at_k


def test_rc10_catalog_quality_and_ranking_flow():
    # 1. Evaluate catalog clearance and freshness
    clock = datetime(2026, 11, 5, 12, 0, 0, tzinfo=UTC)
    product_a = {
        "merchant_id": "m1",
        "source_product_id": "sp1",
        "canonical_product_id": "cp1",
        "category": "dress",
        "image_reference": "img://products/cp1.jpg",
        "source_clearance": True,
        "price": 2499,
        "currency": "INR",
        "price_updated_at": "2026-11-05T10:00:00+00:00",
    }
    eval_a = evaluate_product(product_a, reference_time=clock)
    assert eval_a.passed
    assert eval_a.score == 1.0

    # 2. Uncleared product rejected
    product_b = dict(product_a, source_clearance=False, source_product_id="sp2")
    eval_b = evaluate_product(product_b, reference_time=clock)
    assert not eval_b.passed
    assert "source_not_cleared" in eval_b.errors

    # 3. Recommendations evaluation: verify ranking metrics
    ranked_relevances = [3.0, 2.0, 0.0, 1.0]
    ideal_relevances = [3.0, 2.0, 1.0, 0.0]
    ndcg = ndcg_at_k(ranked_relevances, ideal_relevances, k=4)
    assert ndcg > 0.90

    # 4. Precision at top-2
    prec_2 = precision_at_k([True, True, False, True], 2)
    assert prec_2 == 1.0


def test_rc10_beta_gates_fail_closed_contract():
    # When any gate is missing, decision must be HOLD
    partial_gates = {
        "B1_complete_journey": True,
        "B2_catalog_permissions": True,
    }
    decision = evaluate_beta_gates(partial_gates)
    assert decision.decision == "HOLD"
    assert "B3_recommendation_quality" in decision.missing
