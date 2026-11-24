# Phase 07.6 Verification & Test Matrix

## 1. Test Coverage Summary

Phase 07.6 is validated by 43 automated unit tests executed via `tests/unit/tryon/cache/run_all_cost_control_tests.py`:

```
===========================================================================
RUNNING PHASE 07.6 CACHING AND COST CONTROL TEST SUITE
===========================================================================
PHASE 07.6 SUMMARY: 43 passed, 0 failed, total 43
===========================================================================
```

Combined with Phase 07.5 reliability tests (61 tests), the try-on pipeline maintains **104 passing tests**.

---

## 2. Test Case Mapping

### 2.1 Cache Identity & Hash Integrity (`test_cache_keys.py`)

| Test ID | Method Name | Verification Objective | Result |
|---|---|---|---|
| CACHE-001 | `test_identical_parameters_produce_identical_key` | Same inputs produce identical SHA-256 hash | PASS |
| CACHE-002 | `test_different_user_produces_different_key` | Different user_id produces completely different key (isolation) | PASS |
| CACHE-003 | `test_different_product_produces_different_key` | Changing canonical_product_id alters hash | PASS |
| CACHE-004 | `test_different_shopper_image_hash_produces_different_key` | Changing shopper image bytes alters hash | PASS |
| CACHE-005 | `test_different_garment_image_hash_produces_different_key` | Changing garment image bytes alters hash | PASS |
| CACHE-006 | `test_different_shopper_version_produces_different_key` | Shopper asset version increment alters hash | PASS |
| CACHE-007 | `test_different_garment_version_produces_different_key` | Garment asset version increment alters hash | PASS |
| CACHE-008 | `test_different_provider_produces_different_key` | Provider switch alters hash | PASS |
| CACHE-009 | `test_different_model_produces_different_key` | Model switch alters hash | PASS |
| CACHE-010 | `test_different_model_version_produces_different_key` | Model version bump alters hash | PASS |
| CACHE-011 | `test_different_config_version_produces_different_key` | Render config version alters hash | PASS |
| CACHE-012 | `test_different_preprocessing_version_produces_different_key` | Preprocessing algorithm version alters hash | PASS |
| CACHE-013 | `test_different_policy_version_produces_different_key` | Safety policy version alters hash | PASS |
| CACHE-014 | `test_different_garment_category_produces_different_key` | Garment category changes hash | PASS |
| CACHE-015 | `test_output_options_ordering_does_not_affect_key` | Output options dictionary order is normalized | PASS |
| CACHE-016 | `test_different_output_options_produce_different_key` | Different output options generate distinct key | PASS |
| CACHE-017 | `test_invalid_shopper_hash_raises_value_error` | Non-hex or bad length shopper hash fails fast | PASS |
| CACHE-018 | `test_invalid_garment_hash_raises_value_error` | Non-hex or bad length garment hash fails fast | PASS |
| CACHE-019 | `test_negative_version_raises_value_error` | Version < 1 fails fast | PASS |
| CACHE-020 | `test_empty_required_field_raises_value_error` | Missing required fields fail validation | PASS |

### 2.2 Cache Service & Isolation (`test_cache_service.py`)

| Test ID | Method Name | Verification Objective | Result |
|---|---|---|---|
| CACHE-SVC-001 | `test_cache_miss_when_not_found` | Returns hit=False when key absent | PASS |
| CACHE-SVC-002 | `test_cache_hit_authorized_owner` | Returns hit=True and increments hit count for owner | PASS |
| CACHE-SVC-003 | `test_cache_security_violation_raises` | Raises CacheSecurityError on cross-user access | PASS |
| CACHE-SVC-004 | `test_cache_miss_when_expired` | Expired entry returns hit=False and transitions to EXPIRED | PASS |
| CACHE-SVC-005 | `test_cache_miss_when_invalidated` | Invalidated entry returns hit=False | PASS |
| CACHE-SVC-006 | `test_invalidation_by_product` | Invalidation service purges product entries | PASS |
| CACHE-SVC-007 | `test_invalidation_by_user_consent` | Consent withdrawal purges user entries | PASS |

### 2.3 Rate Limits & Concurrency (`test_rate_limits.py`)

| Test ID | Method Name | Verification Objective | Result |
|---|---|---|---|
| RATE-001 | `test_user_within_burst_limit_succeeds` | Permits up to 5 requests in 10-minute window | PASS |
| RATE-002 | `test_user_burst_limit_rejection` | Rejects 6th request with USER_BURST_10M (HTTP 429) | PASS |
| RATE-003 | `test_user_daily_limit_rejection` | Rejects 21st request with USER_DAILY_24H | PASS |
| RATE-004 | `test_user_concurrency_ceiling` | Caps in-flight jobs at 2 per user | PASS |
| RATE-005 | `test_user_concurrency_release` | Releasing job allows next job acquisition | PASS |
| RATE-006 | `test_merchant_rate_burst` | Rejects 61st request in 1-minute window | PASS |
| RATE-007 | `test_merchant_concurrency_ceiling` | Caps in-flight jobs at 20 per merchant | PASS |
| RATE-008 | `test_rate_limit_exceeded_payload_and_headers` | Verifies Retry-After, Limit, and JSON structure | PASS |

### 2.4 Budgets, Usage & Monitoring (`test_budget_and_usage.py`)

| Test ID | Method Name | Verification Objective | Result |
|---|---|---|---|
| BUDGET-001 | `test_budget_reservation_within_limit_succeeds` | Reserves funds within limit | PASS |
| BUDGET-002 | `test_budget_reservation_exceeding_limit_raises` | Raises BudgetExceededError on overspend | PASS |
| BUDGET-004 | `test_commit_reservation` | Debits reserved spend and credits current spend | PASS |
| BUDGET-005 | `test_release_reservation` | Restores reserved funds without debiting | PASS |
| USAGE-001 | `test_usage_ledger_recording_and_idempotency` | Records provider usage with units and cost | PASS |
| USAGE-002 | `test_usage_ledger_recording_and_idempotency` | Duplicate provider request ID is deduplicated | PASS |
| USAGE-003 | `test_cost_estimation_and_savings` | Resolves unit prices and computes cache ROI | PASS |
| MONITOR-001 | `test_anomaly_detector_budget_thresholds` | Triggers 70% WARN, 90% CRIT, 100% EXCEEDED | PASS |
| MONITOR-002 | `test_anomaly_detector_spend_velocity` | Detects 3x spend acceleration over baseline | PASS |
