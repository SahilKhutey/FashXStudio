# RC05 Implementation Task List & Tracking Register

**Target Branch:** `recovery/rc05-vto-integration`  
**Base Commit:** `db2609e4a8ae3c6fe687c03d81e54ddad86d1f59`  
**Status:** Completed (Pending Final PR Review)

---

## RC05.0 — Baseline & VTO Audit
- [x] Create RC05 branch from `main` (`recovery/rc05-vto-integration`)
- [x] Run baseline backend test suites (`90/90 passed`)
- [x] Run baseline mobile test suites (`21/21 suites, 152/152 passed`, `tsc --noEmit` 0 errors)
- [x] Inventory VTO routes, schemas, database models, and settings
- [x] Trace job dispatch, worker execution, and artifact retrieval path

## RC05.1 — Provider Configuration & Licensing Gates
- [x] Validate mock adapter configuration in development
- [x] Enforce fail-closed policy: reject unknown provider (`ValueError: Unknown or unsupported tryon_provider`)
- [x] Enforce fail-closed policy: reject unimplemented `fashn_selfhost` (`NotImplementedError`)
- [x] Enforce production license gate (`Rule I08: Mock not allowed in production`)
- [x] Enforce `FASHN_API_KEY` requirement when `TRYON_PROVIDER=fashn_api`
- [x] Add automated test suite `tests/unit/test_rc05_provider_configuration.py` (5/5 passed)

## RC05.2 — Input Validation & Consent Verification
- [x] Verify active portrait photo resolution and owner check
- [x] Enforce `body_photo` consent prerequisite before queuing (`RC05-T01: ConsentRequiredError`)
- [x] Reject foreign user photos (`RC05-T02: ValidationError`)
- [x] Reject unaccepted portrait photos (`RC05-T03: ValidationError`)
- [x] Validate garment eligibility and category restrictions (`RC05-T04: ApiError 422 unsupported_garment`)
- [x] Re-verify consent immediately prior to inference (`RC05-T14/T15`)

## RC05.3 — Job Lifecycle & Caching
- [x] Enforce idempotency key replay (`RC05-T05: same job returned`)
- [x] Validate composite cache key calculation (`user_photo_hash`, `garment_id`, `garment_version`, `model_version`, `pipeline_version`, `render_config`)
- [x] Cache hit returns instant completion without re-triggering inference (`RC05-T06`)
- [x] Verified state transitions: `queued -> preprocessing -> inference -> quality_check -> postprocessing -> completed / failed / cancelled`

## RC05.4 — Worker & Queue Reliability
- [x] Implement Dispatcher Observability (`DispatchResult(accepted=bool, reason=...)`) in `ports_dispatch.py`
- [x] Prevent broker outage from stalling HTTP requests (`retry_policy={"max_retries": 0}`)
- [x] Preserve database-persisted jobs during queue dispatch deferral
- [x] Verify worker atomic job claim with row-level locks and lease duration (`lease_seconds=180`)
- [x] Verify periodic lease renewal (heartbeat) and stale job recovery

## RC05.5 — Provider Execution & Recovery
- [x] Normalization and base64/JPEG encoding of person and garment images
- [x] Provider job ID persisted to database *before* polling begins
- [x] Crash recovery: resumed job collects existing `provider_job_id` without duplicate inference (`RC05-T09/T10`)
- [x] Permanent vs retryable error mapping (`provider_auth` -> fatal; `provider_unavailable` -> retry/requeue)

## RC05.6 — Image Preparation
- [x] Person photo preparation and normalization (`ml/prep.py`)
- [x] Garment image normalization and aspect ratio preservation
- [x] Supported category mapping (`tops`, `bottoms`, `one-pieces`)
- [x] Reject corrupt, empty, or un-decodable input bytes

## RC05.7 — Result Validation & Preview Watermarking
- [x] Post-inference quality check (`PostInferenceQualityValidator` checking luminance, contrast, dimensions, and file format)
- [x] Prevent delivery or publication of quality-rejected images
- [x] Visible "PREVIEW ONLY - MOCK VTO" banner embedded into mock adapter output
- [x] C2PA synthetic media metadata embedded via `SyntheticWatermarker`

## RC05.8 — Artifact Storage & Secure Delivery
- [x] User-scoped artifact storage keys: `u/{user_id}/tryon/{job_id}.png`
- [x] Short-lived signed URLs for result image and reference photo
- [x] Strict user isolation on artifact access (`RC05-T13: User B forbidden from accessing User A's artifact`)

## RC05.9 — Mobile Try-On Integration
- [x] Complete state handling in `mobile/app/tryon/[jobId].tsx` (`queued`, `processing`, `quality_check`, `completed`, `failed`, `cancelled`)
- [x] Explicit preview banner displayed for mock provider
- [x] Before/after reference comparison toggle
- [x] Failure reason display and retry action with fresh idempotency key

## RC05.10 — Wardrobe & Feedback Integration
- [x] Save completed try-on result directly to closet/wardrobe (`POST /api/v1/wardrobe/items`)
- [x] Submit visual accuracy rating, purchase confidence, and issue tags (`POST /api/v1/feedback/tryon`)
- [x] Verified associate garment ID and artifact ID persistence

## RC05.11 — Privacy & Resilience
- [x] Mid-flight consent revocation cancels job without publishing artifact (`RC05-T14/T15`)
- [x] Clean deletion of pending artifact if consent is revoked during upload
- [x] Cross-tenant isolation verified across all VTO endpoints

## RC05.12 — E2E Acceptance Verification
- [x] Full VTO unit test suite: 105 passed (`pytest`)
- [x] Contract and integration suites: 9 passed (`pytest`)
- [x] Full mobile test suite: 21 suites, 152 tests passed (`jest --ci`)
- [x] Mobile TypeScript typecheck: 0 errors (`tsc --noEmit`)
- [x] Full VTO smoke test: 8/8 passed (`scripts/rc05_vto_smoke.py`)
