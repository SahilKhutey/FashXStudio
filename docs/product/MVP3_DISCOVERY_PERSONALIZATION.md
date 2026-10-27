# MVP 3: Discovery & Personalization Verification

## Implementation Overview

MVP 3 hardens the catalog feed candidate query, ensures interaction signals are transactional and fail-closed, connects taste signals and style quiz picks into vector personalization, grounds explainable scoring and reason chips, and enforces user-scoped exclusions.

### Key Changes
1. **Catalog Feed Candidates Hardening**:
   - `CanonicalGarmentRepository.list_feed_candidates()` enforces that candidate garments must originate from cleared catalog sources (`status == "cleared"`), possess verified display permissions (`rights_display == True`), have active merchant products (`status == "active"`), active canonical garments (`active == True`), and currently in-stock canonical garments and offers (`in_stock == True`).

2. **Transactional & Fail-Closed Interaction Signals**:
   - `POST /api/v1/feed/signals` enforces authenticated principal verification via `get_principal`.
   - Removed silent exception swallowing (`except Exception: pass`); database session commits transactionally and invalidates user discovery cache.

3. **Style Quiz Picks & Interaction Signal Taste Vector Integration**:
   - `GenerateFeedUseCase` resolves user interaction signals (`FeedSignal`) and onboarding preference selections (`StyleQuizPick`).
   - Liked garments feed into `compute_taste_vector()` with exponential decay weighting.

4. **Explainable Scoring Engine & Reason Chips**:
   - Added module `backend/fashx/recommendation/scoring.py` with `compute_explainable_score` and `fallback_text_embedding`.
   - Generates grounded, validated reason chips ("Top Pick", "Style Match", "Harmony", "Cut") strictly based on real feature contributions, eliminating hallucinated justifications.
   - Relevance scores are strictly normalized and bounded in `[0.0, 1.0]`.

5. **User-Scoped Exclusions**:
   - Negative signals (`hide`, `not_interested`, `dislike`) and style quiz dislikes are dynamically merged into `FilterCriteria.excluded_garment_ids`.
   - `DeterministicFilter` prunes excluded garments prior to ranking.

## Automated Test Verification

Command:
```powershell
pytest tests/unit/test_mvp3_discovery_personalization.py tests/unit/test_recommendation_use_case.py tests/unit/test_recommendation_filters.py tests/unit/test_personalization_ranking.py -q
```

Output:
```
tests/unit/test_mvp3_discovery_personalization.py ....                   [ 26%]
tests/unit/test_recommendation_use_case.py .                             [ 33%]
tests/unit/test_recommendation_filters.py .....                          [ 66%]
tests/unit/test_personalization_ranking.py .....                         [100%]
15 passed
```
