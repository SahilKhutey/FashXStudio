# RC10-D: Recommendation Quality and Explainability

## 1. Objectives
Ensure recommendation ranking delivers high relevance, aesthetic diversity, size availability, and explainable personalized discovery without fabricating similarity metrics for un-embedded items.

## 2. Evaluation Metrics
[`scripts/rc10/evaluate_recommendations.py`](file:///c:/Users/ASUS/Documents/FashXStudio/scripts/rc10/evaluate_recommendations.py) provides verified mathematical evaluation functions:
- **DCG@k**: Discounted Cumulative Gain:
  $$\text{DCG}@k = \sum_{i=1}^k \frac{r_i}{\log_2(i + 1)}$$
- **nDCG@k**: Normalized Discounted Cumulative Gain comparing candidate ranking against ideal ranking:
  $$\text{nDCG}@k = \frac{\text{DCG}@k}{\text{IDCG}@k}$$
- **Precision@k**: Fraction of top-$k$ items satisfying relevance thresholds.
- **Recall@k**: Fraction of total relevant items captured within top-$k$.

## 3. Grounded Explainability
- Explanations must cite explicit user signals (e.g. "Matches your preference for casual summer dresses" or "Similar aesthetic to saved wardrobe items").
- Items missing 512-dimension visual embeddings must not receive manufactured similarity scores; they fall back cleanly to collaborative or category ranking with clear logging.

## 4. Change Control & Rollback Safeguards
Before adjusting ranker weights:
1. Freeze and snapshot baseline ranker weights.
2. Evaluate baseline against the pre-registered judgment dataset.
3. Evaluate candidate weights against the identical dataset.
4. Verify nDCG@10 does not regress.
5. Retain instant rollback configuration flag in `ReleaseConfig`.
