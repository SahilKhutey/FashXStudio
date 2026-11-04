# RC07 — Scoring Engine & Ranking Weights

## 1. Objective
Define an explainable, multi-attribute scoring function with dynamic reweighting for missing features, guaranteeing normalized scores in $[0.0, 1.0]$.

## 2. Ranking Weights Formulation
- **Module**: `backend/fashx/discovery/scoring.py`
```python
@dataclass(frozen=True)
class RankingWeights:
    style: float = 0.18
    occasion: float = 0.10
    color: float = 0.10
    size: float = 0.18
    budget: float = 0.14
    freshness: float = 0.10
    semantic: float = 0.15
    tryon: float = 0.05
```
$$\sum_{k} w_k = 0.18 + 0.10 + 0.10 + 0.18 + 0.14 + 0.10 + 0.15 + 0.05 = 1.00$$

## 3. Dynamic Reweighting
When an attribute (such as `semantic_score`) is missing or unavailable, the system omits its weight $w_{\text{semantic}}$ from the denominator rather than injecting synthetic neutral scores:

$$\text{FinalScore}(g, u) = \frac{\sum_{k \in \text{Available}} w_k \cdot s_k(g, u)}{\sum_{k \in \text{Available}} w_k}$$

Properties:
- Pure cold-start candidates (without semantic vectors) are evaluated purely on available deterministic preferences (style, occasion, color, size, budget, freshness, try-on).
- Score is guaranteed to fall in $[0.0, 1.0]$.

## 4. Verification
Unit test `tests/unit/test_rc07_scoring.py` verifies:
- Weight sum invariant equals 1.0.
- Cosine similarity boundaries: identical vectors (1.0), orthogonal (0.0), opposite (-1.0), non-finite handling (None).
- Dynamic reweighting produces equivalent normalization when semantic score is omitted.
