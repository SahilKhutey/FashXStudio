# ADR-0006: Discovery Ranking Architecture and Evaluation Thresholds

- **Status:** Accepted
- **Date:** 2026-10-10
- **Owner:** Sahil Khutey

---

## 1. Context

The discovery feed is the core user touchpoint of FashXStudio. To be effective, the feed must be relevant, diverse, fast, explainable, and measured against real catalog data. Hard rules (size, budget, gender, source clearance status, price freshness, exclusions, and adult age boundary) must never be violated under any ranking model.

Furthermore, every ranking modification must be judged empirically against pre-registered quantitative benchmarks rather than subjective impressions.

---

## 2. Decision & Architecture

### Multi-Stage Pipeline
1. **Stage 1 (Deterministic Candidate Retrieval & Hard Filtering):**
   - Retrieves candidates matching user gender, active status, cleared source status, price freshness ($\le 72\text{h}$), size availability (`sizes_in_stock`), and excluding saved/hidden garments.
   - Enforces relaxation ladder only when surviving items fall below the page limit (widen budget by 25%, related categories, drop occasion constraint). Hard constraints (size, gender, stock, clearance, kids) never relax.
2. **Stage 2 (Multimodal Scoring):**
   - Vectorized feature computation across 11 normalized dimensions in $[0, 1]$: `taste`, `style`, `occasion`, `formality`, `color`, `skin_harmony`, `size_fit`, `price`, `freshness`, `popularity`, `tryon`.
   - Weights loaded from versioned config (`backend/fashx/discovery/weights/v1.yml`), eliminating magic numbers in application code.
   - Soft priors (e.g. skin-tone harmony) remain low-weighted ($0.10$) and never filter products.
3. **Stage 3 (Constrained Diversity & MMR):**
   - Maximal Marginal Relevance (MMR) balancing relevance and visual/category diversity.
   - Strict caps: $\le 3$ items per brand, $\le 60\%$ per source, and sub-category diversification ($\ge 5$ distinct sub-categories in top 20).
4. **Stage 4 (Truthful Explanations & Stable Pagination):**
   - Explanations generated strictly from features with significant contribution ($\ge 0.05$) and high score ($\ge 0.60$).
   - 15-minute cached ranking session in Redis with signed cursor tokens to prevent duplicates or missing items across pages.

---

## 3. Pre-Registered Acceptance Thresholds

| Measure | Pre-Registered Threshold | Purpose |
|---|---|---|
| **Hard-Rule Violations** | **0** across 200 random personas × 3 pages | Zero tolerance for budget, size, gender, stale price, or hidden item leakage |
| **Feed p95 Latency (Real Catalog)** | **≤ 300 ms** (5 concurrent users) | Interactive feed response SLA |
| **Feed p95 Latency (100k Synthetic)** | **≤ 500 ms** | Scalability headroom |
| **nDCG@10 on Held-Out Personas** | **≥ 0.05** above taste-only baseline & **≥ 0.65** absolute | Demonstrates ranking machinery outperforms simple cosine retrieval |
| **Precision@10 (Rating ≥ 2)** | **≥ 0.60** | Top-10 recommendations fit persona brief |
| **Diversity in Top 20** | **≥ 5** distinct sub-categories, **≤ 3** per brand, **≤ 60%** per source | Avoids single-style or single-brand echo chambers |
| **In-Size Coverage** | **≥ 70%** (sizes S–XL) | Guarantees shoppability in user size |
| **Explanation Truthfulness** | **100%** of reasons map to contributing features | Defends against fabricated styling claims |
| **Cold-Start Diversity (p11)** | **≥ 5** sub-categories, **≤ 40%** in any single category | Exploratory first session without user history |
| **Fairness** | No segment slice **> 0.10** below the mean | Demographic and style parity |

---

## 4. Decision Rule for Model Updates

A new ranker version ($v_{n+1}$) ships to production only if:
1. It achieves **0 hard-rule violations** in the invariant test suite.
2. It improves **nDCG@10 on held-out personas by $\ge 0.02$** over the active baseline ($v_n$).
3. All diversity, latency, and truthfulness criteria are satisfied.

If a new version fails these conditions, the active version is retained and learnings are documented.
