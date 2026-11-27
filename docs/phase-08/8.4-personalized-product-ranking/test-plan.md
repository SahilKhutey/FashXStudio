# Phase 08.4 Test Plan

- `tests/unit/ranking/test_ranking_engine.py`: Category relevance (exact/related/broad/unrelated/unknown), style & colour confidence/conflict guards, `Decimal` price scoring & currency mismatch, merchant-specific size availability, eligibility gates (takedown, out-of-stock, stale, unpermitted), visual similarity compatibility, explicit feedback vs passive views, quality cold-start & sponsored neutrality, scorer normalization & validation, determinism & cache hit/invalidation.
- `tests/unit/ranking/test_ranking_api_and_evaluation.py`: FastAPI endpoint flow (`/ranking/config`, `/shopper/preferences`, `/ranking/products`, `/products/{id}/feedback`), offline metrics (`dcg_at_k`, `ndcg_at_k`, `precision_at_k`, `reciprocal_rank`), and `build_ranking_comparison_report`.
- `mobile/__tests__/ranking.test.tsx`: Mobile ranking API client & `RankingReasonBadges` rendering (with no fit-guarantee language).
