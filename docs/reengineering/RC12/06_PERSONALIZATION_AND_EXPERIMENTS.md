# RC12: Personalization & Experiment Governance

## 1. Ranker Baseline
The active ranking algorithm calculates candidate scores across visual similarity (512-dimension vector cosine distance), category affinity, size match, and budget alignment.

## 2. Evaluation Dimensions
Monitored via [`scripts/rc10/evaluate_recommendations.py`](file:///c:/Users/ASUS/Documents/FashXStudio/scripts/rc10/evaluate_recommendations.py):
- **nDCG@10**: Normalized Discounted Cumulative Gain against human-annotated relevance judgments.
- **Precision@10** & **Recall@10**: Top-10 relevant garment retrieval density.
- **Coverage & Diversity**: Distinct brand, style, and color distribution.

## 3. Experiment Pre-Registration
- Hypotheses, guardrail metrics, and sample targets must be committed to the repository before live cohort activation.
- During any active measurement window (such as the frozen RC11 pilot), scoring weights, MMR parameters, and taste vector logic are strictly frozen.
