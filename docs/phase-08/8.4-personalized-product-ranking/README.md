# Phase 08.4 — Personalized Product Ranking

## Objective
Implement a deterministic, eligibility-first, explainable, and privacy-aware personalized product ranking engine for FashXStudio.

## Scope Implemented
- **Contracts & Config** (`backend/fashx/ranking/contracts.py`, `enums.py`, `config.py`): Versioned request/response schemas (`personalized-v1`, `baseline-v1`), `RankingCandidate`, `RankingFeatures`, `FeatureProvenance`, `EligibilityResult`.
- **Feature Engines**: Category relevance (`category.py` integrated with Phase 06 `TaxonomyRegistry`), style preferences (`style.py`), colour preferences (`color.py`), `Decimal` price preference (`price.py`), canonical availability (`availability.py`), merchant-specific size availability (`size.py`), compatible/authorized visual similarity (`visual_similarity.py`), explicit product feedback (`feedback.py`), and product/merchant quality controls (`quality.py`).
- **Eligibility & Scoring** (`eligibility.py`, `features.py`, `scorer.py`, `explanations.py`, `service.py`, `cache.py`): Hard eligibility checks execute prior to scoring; missing optional features are excluded from the weight denominator; deterministic tie-breaking and evidence-backed reason labels are enforced.
- **Persistence & Erasure** (`database/models/ranking.py`, `0059_add_personalized_ranking_tables.py`, `backend/fashx/application/erasure.py`): Tables `product_feedback`, `shopper_ranking_preferences`, `ranking_events`, and `ranking_evaluation_runs`, with user-linked tables classified under `ACCOUNT_TABLES`.
- **API & Mobile** (`backend/fashx/api/v1/ranking.py`, `mobile/src/features/ranking/`): Shopper-authenticated ranking, preferences, and feedback endpoints plus admin preview (`/api/v1/ranking/preview`).
- **Offline Evaluation** (`backend/fashx/ranking/evaluation/`): NDCG@K, Precision@K, Recall@K, MRR, safety leakage checks, and baseline-vs-personalized comparison reports.

## Completion Status
- Specification: Prepared
- Core Implementation & Unit Tests: Implemented locally (Postgres `alembic check` and remote CI verification pending)
- Offline Staging / A/B Evaluation: Pending staging dataset & execution
