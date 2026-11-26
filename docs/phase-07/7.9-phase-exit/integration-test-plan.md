# Phase 07 Integration Test Plan

## 1. Test Objectives & Scope

The Phase 07 Integration Test Plan exercises the complete virtual try-on workflow across all integrated subsystems:
1. Shopper authentication and identity validation.
2. Asset permission, consent, and technical image validation.
3. Durable job creation, parameter fingerprinting, and transactional outbox.
4. Worker dequeue, lease acquisition, and Time-of-Use guard.
5. Provider adapter submission and external response handling.
6. Sanitized result download, EXIF stripping, and private S3 storage.
7. Owner-authorized retrieval and mandatory visual try-on disclosures.
8. Shopper feedback submission and quality triage linkage.

---

## 2. Core End-to-End Test Scenarios

### Scenario E2E-01: Happy Path Standard Virtual Try-On
- **Preconditions**:
  - Authenticated shopper `shopper-001` with active VTO third-party processing consent.
  - Consented frontal portrait photo (`512x768`, JPEG, valid face detected).
  - Active merchant product with licensed garment photo (`category="casual_shirts"`, `IMAGE_AI_PROCESS` and `VTO_PROCESS` granted).
- **Execution**:
  1. POST `/tryon/jobs` with `shopper_photo_id`, `garment_id`, and `idempotency_key`.
  2. Verify HTTP 201 Created with job status `CREATED`, outbox event written.
  3. Worker dequeues message, transitions state to `VALIDATING` -> `QUEUED` -> `PROCESSING`.
  4. Time-of-Use guard passes; provider adapter submits inference request.
  5. Provider returns completion signal; worker downloads output, validates dimensions, strips EXIF, stores in private S3 bucket.
  6. Job transitions `OUTPUT_VALIDATING` -> `STORING_RESULT` -> `COMPLETED`.
  7. GET `/tryon/jobs/{job_id}` returns signed result URL with `result_type: "VISUAL_TRY_ON"` and `fit_verified: false`.
- **Expected Result**: Complete workflow succeeds in under target SLA; ledger records provider cost.

### Scenario E2E-02: Idempotent Submission & Conflict Rejection
- **Case A (Exact Replay)**: Resubmission with identical `idempotency_key` and identical parameters returns HTTP 200 with existing job record. No secondary inference job is created.
- **Case B (Parameter Mismatch)**: Resubmission with identical `idempotency_key` but differing `garment_id` returns HTTP 409 Conflict.

### Scenario E2E-03: Revocation Race Condition (Time-of-Use Guard)
- **Execution**:
  1. Job is created in `CREATED` state.
  2. Before worker acquires row lock, shopper revokes consent or merchant removes product image.
  3. Worker acquires lease and executes Time-of-Use guard.
  4. Guard detects revoked permission and halts immediately.
  5. Job transitions to `FAILED` with error code `CONSENT_REVOKED` or `LICENSE_REVOKED`.
- **Expected Result**: No external provider request is sent; no billing charges incurred.

### Scenario E2E-04: Unauthorized Cross-User Access (Tenant Isolation)
- **Preconditions**: Job `job-alpha` created by `shopper-001`.
- **Execution**:
  - `shopper-002` attempts GET `/tryon/jobs/job-alpha`.
- **Expected Result**: HTTP 404 Not Found returned (avoiding information leakage on job existence).

### Scenario E2E-05: Prohibited Fit Claim Rejection
- **Preconditions**: Client attempts to render try-on output with widget label "Your Guaranteed Fit".
- **Execution**: `enforce_merchant_widget_policy()` is invoked.
- **Expected Result**: Label is automatically sanitized to "AI-generated visual try-on", `disclaimer_locked` set to `True`, and `allow_fit_guarantee` set to `False`.

---

## 3. Test Suites & Execution Command

All integration test suites are consolidated under `tests/unit/tryon/run_phase07_exit_gate.py`:
- `tests/unit/tryon/validation/run_all_validation_tests.py` (31 tests)
- `tests/unit/tryon/lifecycle/run_all_lifecycle_tests.py` (26 tests)
- `tests/unit/tryon/lifecycle/run_all_reliability_tests.py` (61 tests)
- `tests/unit/tryon/cache/run_all_cost_control_tests.py` (43 tests)
- `tests/unit/tryon/evaluation/run_all_evaluation_tests.py` (24 tests)
- `tests/unit/tryon/separation/run_all_separation_tests.py` (67 tests)
- `tests/unit/tryon/exit_gate/test_phase07_exit_gate.py` (8 tests)

**Execution Command**:
```bash
python tests/unit/tryon/run_phase07_exit_gate.py
```
**Execution Outcome**: 260 tests passed, 0 failed (14.63s execution time).
