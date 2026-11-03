# RC-01 — Catalog & Feed Recovery

## Problem Statement
The initial audit identified that the feed was consistently returning 0 items, and production deployments would crash upon cold start or feed retrieval.

## Defect Analysis & Root Causes

### 1. FX-007: Unconditional `FakeEmbedder` Instantiation
- **File**: `backend/fashx/recommendation/application/generate_feed.py`
- **Root Cause**: `GenerateFeedUseCase` imported and instantiated `FakeEmbedder()`. The constructor of `FakeEmbedder` explicitly raises `RuntimeError("FakeEmbedder is strictly forbidden in environment 'prod'")`. Consequently, any production invocation crashed immediately.

### 2. FX-008: Broad Exception Suppression
- **File**: `backend/fashx/recommendation/application/generate_feed.py`
- **Root Cause**: Multiple `except Exception: pass` blocks surrounded critical queries:
  - Reading onboarding profiles.
  - Reading feed signals (`FeedSignal`).
  - Reading wardrobe items (`WardrobeItem`).
  - Reading style quiz picks (`StyleQuizPick`).
  - Reading exclusions (`FeedExclusion`).
  Any schema error, query typo, or connection timeout was silently discarded, causing the use case to behave as if the user had empty taste profiles while obscuring infrastructure bugs.

### 3. FX-009: Missing Empty-Feed Diagnostics
- **Root Cause**: When 0 items survived filtering, the endpoint returned an empty list without indicating why (empty catalog, gender mismatch, budget cutoff, or category mismatch).

### 4. Client-to-Backend Contract Misalignment
- **Mobile Behavior**: In `mobile/app/onboarding/profile.tsx`, the onboarding wizard submitted `categories: v.occasions` (e.g. `["casual", "work"]` instead of canonical garment categories `["top", "bottom", "one_piece"]`) and `budget_max: 5000` (in Indian Rupees rather than minor units `500000`).
- **Result**: The deterministic filter eliminated 100% of candidates because `offer.price_cents` (~149900) was greater than the filtering threshold 5000.

## Implementation Details

### Changes to `backend/fashx/recommendation/application/generate_feed.py`:
1. **Removed `FakeEmbedder`**: Completely eliminated import and instantiation of `FakeEmbedder`.
2. **Taste Signals from Persisted Embeddings**: If a user has positive signals (liked items, quiz picks), their taste vector is computed strictly from the valid `garment_enrichments.embedding` vector stored in the database.
3. **Structured Observability**: Replaced silent `except Exception: pass` with explicit logging:
   ```python
   logger.warning("Could not load feed signals for user %s: %s", user_id, exc)
   ```
4. **Structured Empty Diagnostics**: Added `empty_reason` to the feed output:
   - `"catalog_empty"`: If zero candidates exist in the database.
   - `"all_candidates_filtered"`: If candidates exist but were removed by deterministic filters (category, gender, budget).

## Verification Results
1. **Unit Test**: `tests/unit/test_recommendation_use_case.py`
   - `test_feed_cold_start_does_not_use_fake_embedder` 🟢 Passed in `ENV=prod`.
   - `test_empty_feed_reports_catalog_empty` 🟢 Passed.
2. **Live Feed Response**:
   - Query: `GET http://127.0.0.1:8000/api/v1/feed` with `Authorization: Bearer dev-user-1`.
   - Result: 20 live candidates returned with full images, brand titles, prices, and stylist explanations.
