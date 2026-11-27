"""API, cross-shopper isolation, and baseline comparison evaluation tests (Phase 08.4)."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from fashx.api.v1.ranking import admin_router, get_ranking_service, get_ranking_store, router
from fashx.ranking.cache import RankingCache
from fashx.ranking.contracts import (
    CandidateVariant,
    RankingCandidate,
    RankingContext,
    ShopperPreferenceSnapshot,
)
from fashx.ranking.evaluation.comparison import evaluate_ranking_version
from fashx.ranking.evaluation.dataset import JudgedQueryPair
from fashx.ranking.evaluation.metrics import dcg_at_k, ndcg_at_k, precision_at_k, reciprocal_rank
from fashx.ranking.evaluation.report import build_ranking_comparison_report
from fashx.ranking.repository import InMemoryRankingStore
from fashx.ranking.service import PersonalizedRankingService
from fashx.security.deps import Principal, get_principal
from tests.unit.ranking.test_ranking_engine import _base_candidate, _make_taxonomy


def _build_test_client(store: InMemoryRankingStore, user_id: str) -> TestClient:
    app = FastAPI()
    svc = PersonalizedRankingService(taxonomy=_make_taxonomy(), cache=RankingCache())
    app.dependency_overrides[get_principal] = lambda: Principal(
        user_id=user_id, issuer="test", subject=user_id, scopes=["read", "write"]
    )
    app.dependency_overrides[get_ranking_store] = lambda: store
    app.dependency_overrides[get_ranking_service] = lambda: svc
    app.include_router(router, prefix="/api/v1")
    app.include_router(admin_router, prefix="/api/v1")
    return TestClient(app)


def test_ranking_api_preferences_feedback_and_cache_invalidation() -> None:
    uid = str(uuid4())
    store = InMemoryRankingStore(
        candidates=[
            _base_candidate(
                product_id="p-navy",
                style_tags={"MINIMAL": 0.95},
                primary_colors=("NAVY",),
                price=Decimal("1199"),
            ),
            _base_candidate(
                product_id="p-oversized",
                style_tags={"OVERSIZED": 0.95},
                primary_colors=("RED",),
                price=Decimal("1200"),
            ),
        ]
    )
    client = _build_test_client(store, uid)

    cfg_res = client.get("/api/v1/ranking/config")
    assert cfg_res.status_code == 200
    assert cfg_res.json()["ranking_version"] == "personalized-v1"

    pref_res = client.patch(
        "/api/v1/shopper/preferences",
        json={
            "style_preferences": [{"style_id": "MINIMAL", "preference": "LIKE", "strength": 1.0}],
            "preferred_colors": ["NAVY"],
            "budget_min": 500,
            "budget_max": 1500,
        },
    )
    assert pref_res.status_code == 200
    assert pref_res.json()["revision"] == 2

    rank_res = client.post(
        "/api/v1/ranking/products",
        json={"context": {"category_id": "SHIRTS", "selected_size": "M"}},
    )
    assert rank_res.status_code == 200
    body = rank_res.json()
    assert [item["product_id"] for item in body["results"]] == ["p-navy", "p-oversized"]

    # Explicit dislike pushes p-navy below or drops its feedback score & invalidates cache
    fb_res = client.post("/api/v1/products/p-navy/feedback", json={"feedback_type": "DISLIKE"})
    assert fb_res.status_code == 201
    get_fb = client.get("/api/v1/products/p-navy/feedback")
    assert len(get_fb.json()) == 1

    del_fb = client.delete("/api/v1/products/p-navy/feedback")
    assert del_fb.status_code == 200
    assert del_fb.json()["removed_count"] == 1


def test_offline_evaluation_metrics_and_baseline_comparison() -> None:
    assert dcg_at_k([3, 2, 0], 3) > 0
    assert ndcg_at_k([0, 0], [0, 0], 5) == 0.0
    assert precision_at_k([3, 1, 2], 3) == 2 / 3
    assert reciprocal_rank([0, 2, 3]) == 0.5

    tax = _make_taxonomy()
    c_pers = RankingCandidate(
        product_id="p-match",
        merchant_id="m1",
        merchant_offer_id="o1",
        title="Navy Minimal Shirt",
        category_id="SHIRTS",
        price=Decimal("1000"),
        variants=(CandidateVariant("v1", "M", "IN_STOCK"),),
        style_tags={"MINIMAL": 0.95},
        primary_colors=("NAVY",),
        image_quality=0.8,
        attribute_completeness=0.8,
        data_freshness=0.8,
        availability_verified_at=datetime.now(UTC),
    )
    c_generic = RankingCandidate(
        product_id="p-generic",
        merchant_id="m2",
        merchant_offer_id="o2",
        title="Oversized Red Shirt",
        category_id="SHIRTS",
        price=Decimal("1000"),
        variants=(CandidateVariant("v2", "M", "IN_STOCK"),),
        style_tags={"OVERSIZED": 0.95},
        primary_colors=("RED",),
        image_quality=0.95,
        attribute_completeness=0.95,
        data_freshness=0.95,
        availability_verified_at=datetime.now(UTC),
    )
    shopper = ShopperPreferenceSnapshot(
        shopper_id="eval-u1",
        liked_styles={"MINIMAL": 1.0},
        disliked_styles={"OVERSIZED": 1.0},
        preferred_colors=frozenset({"NAVY"}),
        budget_min=Decimal("500"),
        budget_max=Decimal("1500"),
    )
    dataset = [
        JudgedQueryPair(
            query_id="q1",
            shopper_profile=shopper,
            context=RankingContext(category_id="SHIRTS", selected_size="M", require_selected_size=True),
            candidates=(c_generic, c_pers),
            relevance_grades={"p-match": 3, "p-generic": 0},
            disliked_product_ids=frozenset({"p-generic"}),
        )
    ]

    report = build_ranking_comparison_report(
        dataset_version="eval-v1",
        dataset=dataset,
        taxonomy=tax,
    )
    assert report.safety_gates_passed is True
    assert report.personalized.ndcg_at_10 >= report.baseline.ndcg_at_10
    assert evaluate_ranking_version(dataset=[], taxonomy=tax, ranking_version="baseline-v1").query_count == 0
