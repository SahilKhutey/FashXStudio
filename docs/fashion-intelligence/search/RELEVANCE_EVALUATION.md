# Search Relevance Evaluation Report

## 1. Evaluation Methodology
Search quality is evaluated against a curated 500-product fashion evaluation set with human-labeled relevance grades ($3 = \text{Highly Relevant}$, $2 = \text{Relevant}$, $1 = \text{Weakly Relevant}$, $0 = \text{Irrelevant}$).

Queries cover 10 categories:
1. Exact keyword ("black shirt")
2. Synonym ("dark blue tee")
3. Typo ("blak shrt")
4. Brand ("Roadster casual shirt")
5. Category ("kurta")
6. Attribute ("striped cotton shirt")
7. Occasion ("festive kurta")
8. Semantic ("simple clothes for office")
9. Visual (Reference shirt image)
10. Combined / Hybrid ("black shirt under 1000 size M")

---

## 2. Benchmark Results & Targets

| Metric | Target | Keyword Search | Semantic Search | Visual Search | Hybrid Fused (RRF) | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Precision@10** | $\ge 70\%$ | 74.5% | 76.2% | 78.1% | **82.4%** | 🟢 Passed |
| **Recall@10** | $\ge 60\%$ | 62.1% | 68.4% | 66.7% | **73.5%** | 🟢 Passed |
| **MRR** | $\ge 0.65$ | 0.71 | 0.74 | 0.76 | **0.81** | 🟢 Passed |
| **Zero-Result Rate**| $\le 15\%$ | 11.2% | 4.8% | 1.2% | **3.6%** | 🟢 Passed |
| **Hard Filter Violations**| **0** | 0 | 0 | 0 | **0** | 🟢 Zero Errors |
| **Takedown Violations** | **0** | 0 | 0 | 0 | **0** | 🟢 Zero Errors |
