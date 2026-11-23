from __future__ import annotations

from typing import Any
from uuid import uuid4

from sqlalchemy.orm import Session

from database.models.catalog_search import SearchEvaluationRunRecord
from fashx.catalog.search.evaluation import QueryJudgment, SearchRelevanceEvaluator


def test_evaluation_perfect_retrieval() -> None:
    """Verify evaluation metric calculations when retrieved candidates match ground truth perfectly."""
    evaluator = SearchRelevanceEvaluator()
    id1, id2 = uuid4(), uuid4()

    judgment = QueryJudgment(
        query="black shirt",
        relevant_ids={id1, id2},
        grades={id1: 3, id2: 2},
    )

    query_results = {
        "black shirt": [id1, id2],
    }

    metrics = evaluator.evaluate(query_results, [judgment])
    assert metrics.precision_at_10 == 0.2  # 2 relevant out of 10 slots
    assert metrics.recall_at_10 == 1.0
    assert metrics.mrr == 1.0
    assert metrics.ndcg_at_10 > 0.95
    assert metrics.zero_result_rate == 0.0


def test_evaluation_partial_and_zero_ranking() -> None:
    """Verify reciprocal rank and zero result rate computation for mixed retrieval."""
    evaluator = SearchRelevanceEvaluator()
    id_rel = uuid4()
    id_irrel = uuid4()

    # Query 1: relevant item at rank 2 -> RR = 0.5
    j1 = QueryJudgment(query="kurta", relevant_ids={id_rel}, grades={id_rel: 3})
    # Query 2: no results -> zero result
    j2 = QueryJudgment(query="spacesuit", relevant_ids={uuid4()})

    query_results = {
        "kurta": [id_irrel, id_rel],
        "spacesuit": [],
    }

    metrics = evaluator.evaluate(query_results, [j1, j2])
    assert metrics.zero_result_rate == 0.5
    # MRR is average of 0.5 and 0.0 = 0.25
    assert metrics.mrr == 0.25


def test_evaluation_persistence(
    search_sync_session: Session, setup_search_catalog: dict[str, Any]
) -> None:
    """Verify evaluation run can be logged into search_evaluation_runs database table."""
    evaluator = SearchRelevanceEvaluator()
    mp1 = setup_search_catalog["mp1"]

    j = QueryJudgment(query="shirt", relevant_ids={mp1.id})
    metrics = evaluator.evaluate({"shirt": [mp1.id]}, [j])

    run_record = evaluator.record_evaluation_run(
        session=search_sync_session,
        metrics=metrics,
        evaluator_version="v1.0.0",
        dataset_size=1,
    )

    assert run_record.id is not None
    assert run_record.evaluator_version == "v1.0.0"
    assert run_record.precision_at_10 == 0.1  # 1 relevant out of 10
    assert run_record.mrr == 1.0

    # Query back
    saved = search_sync_session.get(SearchEvaluationRunRecord, run_record.id)
    assert saved is not None
    assert saved.ndcg_at_10 > 0.0
