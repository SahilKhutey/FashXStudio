# RC07 — MMR Diversification & Catalog Caps

## 1. Objective
Prevent feed monotony (e.g. 10 identical blue shirts from the same brand) by balancing individual garment relevance with diversity across brand and subcategory dimensions.

## 2. Maximal Marginal Relevance (MMR) Formulation
Given ranked candidate pool $R$ and selected items set $S$:

$$\text{MMR}(d_i) = \lambda \cdot \text{Relevance}(d_i) - (1 - \lambda) \cdot \max_{d_j \in S} \text{Sim}(d_i, d_j)$$

- **Default $\lambda$**: 0.70 (configurable between 0.0 and 1.0).
- $\text{Sim}(d_i, d_j)$ is computed via cosine similarity of embeddings when both are present; otherwise using category/color overlap proxies.

## 3. Hard Diversity Caps
In addition to MMR distance penalties, the selector enforces hard caps:
- **Maximum items per brand**: 3
- **Maximum items per subcategory**: 3

If all remaining candidates exceed caps and $|S| < \text{top\_k}$, the next best remaining item is chosen to satisfy the requested page limit.

## 4. Verification
Unit test `tests/unit/test_rc07_scoring.py::test_mmr_diversification_caps` verifies:
- Output length satisfies `top_k`.
- No brand exceeds `max_per_brand = 3`.
- Diversity balances high relevance with variety.
