# RC07 — Evaluation Metrics Report

## 1. Metric Definitions
- **NDCG@K (Normalized Discounted Cumulative Gain)**:
  Measures ranking quality with position-discounted gain against ideal ranking.
- **Precision@K**:
  Fraction of top-K recommended items that are relevant to the user persona.
- **Recall@K**:
  Fraction of total relevant catalog items surfaced in the top-K recommendations.
- **Hard Constraint Violation Rate**:
  Percentage of recommended items in top-K violating budget, size, or negative exclusion constraints. Target: **0.0%**.

## 2. Automated Evaluation Suite
- **Test File**: `tests/evaluation/test_rc07_ranking_metrics.py`
- Command: `.venv\Scripts\pytest.exe tests/evaluation/test_rc07_ranking_metrics.py -v`
- Output:
```
tests/evaluation/test_rc07_ranking_metrics.py::test_ranking_ndcg_and_precision_metrics PASSED [ 50%]
```

## 3. Measured Results (Fixture Catalog Pool)
| Metric | Threshold Target | Measured Value | Status |
|---|---|---|---|
| Hard Constraint Violation Rate | == 0.0% | 0.0% | 🟢 PASS |
| Precision@5 | >= 0.80 | 1.00 (5/5 hits) | 🟢 PASS |
| Recall@5 | >= 0.50 | 0.625 (5/8 hits) | 🟢 PASS |
| NDCG@5 | >= 0.85 | 1.000 | 🟢 PASS |

## 4. Persona Relevance Divergence
- **Test File**: `tests/evaluation/test_rc07_persona_relevance.py`
- Command: `.venv\Scripts\pytest.exe tests/evaluation/test_rc07_persona_relevance.py -v`
- Result:
  - Persona 1 ("Formal Corporate") ranked formal wool blazers top.
  - Persona 2 ("Casual Earth-Tone") ranked casual linen shirts top.
  - Zero cross-persona ranking collision (`top_a['id'] != top_b['id']`).
  - Output: `PASSED [100%]`
