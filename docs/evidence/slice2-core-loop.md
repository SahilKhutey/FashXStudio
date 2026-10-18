# Slice 2 Evidence Card: Core Try-On Loop (Feed, Detail, Try-On & History)

**Branch**: `feat/slice2-feed-detail-tryon`  
**Date**: 2026-10-18  
**Scope**: Personalized feed (`/feed`) with cursor pagination, presentation metadata (`title`, `brand`, `image_url`, `price_updated_at`, `reason_chips`, `tryon_supported`), `empty_reason`, and `relaxed` banner · Feed signals (`/feed/signals`) with 5-second undo snackbar · Session impression analytics batching (`/analytics/session-events`) every 5s or on app background · Garment detail (`/garments/{id}`) with image gallery, size stock chips, affiliate disclosure, merchant Buy link, and gated Try-On action · Asynchronous Try-On job submission (`/tryon/jobs`) with idempotency key and 422 rejection on unsupported garments · Live status polling with exponential backoff (1s to 5s) and 120s "taking longer" warning · Before/after visual comparison toggle · 1–5 visual accuracy rating and "looks off" chips · Try-on history (`/(tabs)/looks`) and virtual closet (`/(tabs)/closet`).

---

## 1. Test Verification Gates

### 1.1 Backend Test Gate
- **Command**: `python -m pytest tests/integration/test_slice2_backend.py -v`
- **Result**: **3 passed in 10.41s**
  - `test_feed_endpoint_pagination_and_fields`: PASSED (verifies cursor pagination slicing, candidate presentation fields, reason chips, price freshness timestamps, and tryon eligibility)
  - `test_analytics_session_events_batch`: PASSED (verifies `POST /api/v1/analytics/session-events` recording batch of client impression events)
  - `test_tryon_jobs_rejects_unsupported_garment_with_422`: PASSED (verifies fail-closed validation rejecting garments where `tryon_supported == False`)

### 1.2 Mobile Unit Test Gate (Jest)
- **Command**: `npm test -- --ci`
- **Result**: **8 test suites passed, 49 tests passed in 6.53s**
  - `__tests__/feed_and_tryon.test.ts`:
    - Stable image cache key generator strips query params and fragments for CDN signed URL caching
    - Visual accuracy rating mapping (1–5 maps to `very_inaccurate` through `very_accurate`)
    - Polling exponential backoff capped at 5000ms (1s -> 2s -> 4s -> 5s)
    - Signal 5-second undo timer cancellation and flush-on-expiry
    - Impression batching deduplication
  - `__tests__/capture_privacy.test.ts`: PASSED
  - `__tests__/file_cleanup.test.ts`: PASSED
  - `__tests__/style_quiz_picks.test.ts`: PASSED
  - `__tests__/quality_reasons.test.ts`: PASSED
  - `__tests__/onboarding_schemas.test.ts`: PASSED
  - `__tests__/dev_token_gate.test.ts`: PASSED
  - `__tests__/auth_and_api.test.ts`: PASSED

### 1.3 Static Analysis & Linter Gates
- **TypeScript**: `npm run typecheck` (`tsc --noEmit`) -> **0 errors**
- **ESLint**: `npx eslint . --max-warnings 0` -> **0 warnings**
- **Python Ruff**: `ruff check backend/ tests/` -> **All checks passed**

---

## 2. Invariants & Contract Enforcement

1. **Strict Try-On Gate (Client & Server)**:
   - On mobile (`app/garment/[id].tsx`), the Try-On button is rendered only when `garment.tryon_supported === true`.
   - On the backend (`backend/fashx/tryon/router.py`), attempts to submit try-on jobs for unsupported garments are rejected with HTTP 422 `ValidationError(field="garment_id")`.
2. **Stable Signed Image Caching**:
   - `useSignedImage` and card rendering derive stable cache keys (`url.split("?")[0]`) so refreshing expired signed URLs does not invalidate image disk cache or cause flickering.
3. **Optimistic Signal Undo Window**:
   - User signals (`not_interested`, `hide`) trigger a 5-second undo snackbar before network dispatch. Tapping "Undo" cancels the timer and suppresses the backend mutation.
4. **Impression Batching & Battery Efficiency**:
   - Viewable garment impressions are deduplicated and flushed in batches every 5 seconds or immediately when the app transitions to the background.
5. **Zero Photo Logging**:
   - Zero image URLs or base64 payloads are emitted to console logs during feed browsing, garment viewing, or try-on rendering.
