# Slice 1 Evidence Card: Mobile Onboarding & Photo Capture

**Branch**: `feat/slice1-onboarding-capture`  
**Date**: 2026-10-18  
**Scope**: Consent (2 explicit consents, adults-only block, legal links) · 3-Step Profile (Zod-validated height, budget, occasions) · Style Quiz (2-column FlashList, min 3 picks rule, dev skip fallback) · Camera Capture (silhouette outline overlay, system library picker fallback, pre-upload resize to 2048px 0.9 JPEG, fail-closed file cleanup, zero logging of photo URIs, quality feedback).

---

## 1. Test Verification Gates

### 1.1 Backend Test Gate
- **Command**: `python -m pytest tests/integration/test_slice1_backend_prep.py tests/contracts/test_mobile_contract.py tests/integration/test_seed_local.py tests/integration/test_catalog_ingestion_parity.py -v`
- **Result**: **19 passed** in 9.67s
  - `test_config_endpoint_returns_consent_version_and_legal`: PASSED
  - `test_reject_reasons_json_matches_enum_stale_file_check`: PASSED
  - `test_photo_upload_without_consent_returns_403_consent_required`: PASSED
  - `test_photo_upload_multipart_form_with_consent_succeeds`: PASSED
  - `test_consent_records_contract_and_boundaries`: PASSED
  - `test_photo_upload_refuses_without_active_consent`: PASSED
  - `test_onboarding_missing_order_table_driven`: PASSED
  - `test_style_quiz_picks_contract`: PASSED
  - `test_customer_garment_detail_contract`: PASSED
  - `test_tryon_jobs_contract_and_user_history`: PASSED
  - `test_erasure_covers_style_quiz_picks_and_consent`: PASSED
  - `test_garment_tryon_eligibility_hotlink_source_is_false`: PASSED
  - `test_consent_endpoint_http_level`: PASSED
  - `test_erasure_injected_failure_rolls_back`: PASSED
  - `test_consent_version_consistent_across_router_me_and_config`: PASSED
  - `test_me_requires_both_consents_and_three_quiz_picks`: PASSED
  - `test_seed_local_catalog_dry_run_apply_and_idempotency`: PASSED
  - `test_seed_refreshes_price_freshness_after_time_advancement`: PASSED
  - `test_ingestion_parity_invariants`: PASSED

### 1.2 Mobile Unit Test Gate (Jest)
- **Command**: `npm test -- --ci`
- **Result**: **7 test suites passed, 39 tests passed**
  - `__tests__/onboarding_schemas.test.ts`: Zod schema bounds, budget min > max rejection, height 119 rejected.
  - `__tests__/quality_reasons.test.ts`: Rejection enum parity, descriptive phrase mapping, fallback to generic.
  - `__tests__/file_cleanup.test.ts`: Safe file deletion, batch cleanup in `finally`, exception resilience.
  - `__tests__/style_quiz_picks.test.ts`: Min 3 picks requirement, submit button enablement, 10-item cap.
  - `__tests__/capture_privacy.test.ts`: Zero photo URIs or image filenames in logs, guaranteed file cleanup.
  - `__tests__/auth_and_api.test.ts`: Auth headers, token injection, error handling.
  - `__tests__/dev_token_gate.test.ts`: Dev login gate and production protection.

### 1.3 Static Analysis & Linter Gates
- **TypeScript**: `npm run typecheck` (`tsc --noEmit`) -> **0 errors**
- **ESLint**: `npx eslint . --max-warnings 0` -> **0 warnings**
- **Python Ruff**: `ruff check` -> **All checks passed**

---

## 2. Invariants & Privacy Protections

1. **Zero Storage Leaks**:
   - Both raw camera capture URIs and resized temporary files are strictly cleaned up in a `finally` block via `cleanupFiles([rawUri, preparedUri])`.
2. **Zero Sensitive Data Logging**:
   - Camera paths, URIs, and binary image payloads are never passed to `console.log`, `console.warn`, or error reporters.
3. **Fail-Closed Adults-Only Consent**:
   - Users under 18 cannot proceed past the consent gate. Hardware back button is suppressed on Android to prevent bypassing consent.
4. **Transparent Multipart & JSON Support**:
   - `POST /api/v1/profile/{user_id}/photos` supports `multipart/form-data` with field `"file"` alongside base64 JSON, enabling native upload progress tracking via `XMLHttpRequest`.
