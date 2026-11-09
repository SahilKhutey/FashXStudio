import pytest

from scripts.rc10.evaluate_recommendations import (
    dcg_at_k,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
)


def test_perfect_ranking_has_ndcg_one():
    values = [3.0, 2.0, 1.0]
    assert ndcg_at_k(values, values, k=3) == pytest.approx(1.0)


def test_reversed_ranking_has_lower_ndcg():
    ideal = [3.0, 2.0, 1.0]
    reversed_values = [1.0, 2.0, 3.0]
    assert ndcg_at_k(reversed_values, ideal, k=3) < 1.0


def test_precision_at_k():
    assert precision_at_k([True, False, True, False], 4) == 0.5


def test_recall_at_k():
    assert recall_at_k([True, False, True], 4, 4) == 0.5


def test_invalid_k_rejected():
    with pytest.raises(ValueError):
        precision_at_k([True], 0)
    with pytest.raises(ValueError):
        recall_at_k([True], 0, 1)
    with pytest.raises(ValueError):
        ndcg_at_k([1.0], [1.0], 0)
    with pytest.raises(ValueError):
        dcg_at_k([1.0], 0)


def test_negative_relevance_rejected():
    with pytest.raises(ValueError):
        dcg_at_k([-1.0], 1)
