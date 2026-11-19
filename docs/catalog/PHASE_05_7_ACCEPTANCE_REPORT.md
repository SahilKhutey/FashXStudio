# Phase 05.7 — Acceptance Report: Initial Catalog Targets and Measurement Framework

## 1. Acceptance Overview
- **Phase:** 05.7 — Initial Catalog Targets
- **Target Objectives:** Establish measurable, evidence-backed catalog targets (`CAT-TGT-01` through `CAT-TGT-07`), deterministic sampling, SSRF protections, release gate evaluation engine, administrative reporting APIs, and immutable evaluation run storage.
- **Delivery Scope:**
  - Database schema & Alembic migration: `0044_add_catalog_evaluation_runs.py` (`catalog_evaluation_runs`, `catalog_link_health_checks`).
  - Catalog metrics engine: `backend/fashx/catalog/metrics/` (`contracts.py`, `target_config.py`, `sampling.py`, `source_metrics.py`, `product_metrics.py`, `price_freshness.py`, `link_health.py`, `image_permission_metrics.py`, `evaluator.py`, `report_service.py`, `router.py`).
  - Admin & Reporting API endpoints: Mounted at `/api/v1/admin/catalog/...` (protected by admin role check).
  - Test suites: `tests/unit/catalog/test_catalog_targets_and_metrics.py` (covering CAT57-001 through CAT57-030) and `tests/unit/catalog/test_catalog_targets_api.py`.
  - Route snapshot integrity: 316 routes verified in `tests/security/routes.snapshot.txt`.

---

## 2. Test Execution and Verification

### 2.1 Unit and Integration Test Results
```
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\ASUS\Documents\FashXStudio
configfile: pytest.ini
plugins: anyio-4.12.1, hypothesis-6.156.6, langsmith-0.14.4, asyncio-1.4.0, cov-7.1.0
asyncio: mode=Mode.AUTO

tests/unit/catalog/test_catalog_targets_and_metrics.py::test_cat57_001_one_approved_live_source_qualifies PASSED [  2%]
tests/unit/catalog/test_catalog_targets_and_metrics.py::test_cat57_002_mock_adapter_source_does_not_qualify PASSED [  5%]
tests/unit/catalog/test_catalog_targets_and_metrics.py::test_cat57_003_expired_authorization_fails_compliance_gate PASSED [  8%]
tests/unit/catalog/test_catalog_targets_and_metrics.py::test_cat57_004_revoked_source_permission_blocks_relevant_operation PASSED [ 11%]
tests/unit/catalog/test_catalog_targets_and_metrics.py::test_cat57_005_1000_valid_offers_pass_initial_product_count PASSED [ 14%]
tests/unit/catalog/test_catalog_targets_and_metrics.py::test_cat57_006_raw_rows_with_duplicates_exclude_duplicates PASSED [ 17%]
tests/unit/catalog/test_catalog_targets_and_metrics.py::test_cat57_007_quarantined_product_excluded_from_usable_count PASSED [ 20%]
tests/unit/catalog/test_catalog_targets_and_metrics.py::test_cat57_008_inactive_offer_excluded_from_usable_count PASSED [ 23%]
tests/unit/catalog/test_catalog_targets_and_metrics.py::test_cat57_009_product_without_valid_merchant_url_excluded PASSED [ 26%]
tests/unit/catalog/test_catalog_targets_and_metrics.py::test_cat57_010_same_garment_across_merchants_counted_separately PASSED [ 29%]
tests/unit/catalog/test_catalog_targets_and_metrics.py::test_cat57_011_price_within_freshness_window_classified_as_fresh PASSED [ 32%]
tests/unit/catalog/test_catalog_targets_and_metrics.py::test_cat57_012_price_beyond_freshness_window_classified_as_stale PASSED [ 35%]
tests/unit/catalog/test_catalog_targets_and_metrics.py::test_cat57_013_missing_price_verification_timestamp_classified_as_unverified PASSED [ 38%]
tests/unit/catalog/test_catalog_targets_and_metrics.py::test_cat57_014_mixed_currencies_retained_explicitly PASSED [ 41%]
tests/unit/catalog/test_catalog_targets_and_metrics.py::test_cat57_015_valid_merchant_destination_url_classified_as_valid PASSED [ 44%]
tests/unit/catalog/test_catalog_targets_and_metrics.py::test_cat57_016_http_404_classified_as_broken PASSED [ 47%]
tests/unit/catalog/test_catalog_targets_and_metrics.py::test_cat57_017_temporary_503_retried_and_not_classified_as_broken PASSED [ 50%]
tests/unit/catalog/test_catalog_targets_and_metrics.py::test_cat57_018_destination_resolving_to_private_ip_blocked PASSED [ 52%]
tests/unit/catalog/test_catalog_targets_and_metrics.py::test_cat57_019_redirect_to_unrelated_or_blocked_destination_classified_invalid PASSED [ 55%]
tests/unit/catalog/test_catalog_targets_and_metrics.py::test_cat57_020_image_missing_permission_evidence_fails_traceability PASSED [ 58%]
tests/unit/catalog/test_catalog_targets_and_metrics.py::test_cat57_021_display_permission_without_storage_permission_blocks_storage PASSED [ 61%]
tests/unit/catalog/test_catalog_targets_and_metrics.py::test_cat57_022_missing_vto_permission_blocks_vto_processing PASSED [ 64%]
tests/unit/catalog/test_catalog_targets_and_metrics.py::test_cat57_023_image_source_under_takedown_blocks_processing PASSED [ 67%]
tests/unit/catalog/test_catalog_targets_and_metrics.py::test_cat57_024_unauthorized_active_source_fails_compliance_gate PASSED [ 70%]
tests/unit/catalog/test_catalog_targets_and_metrics.py::test_cat57_025_zero_unauthorized_sources_passes_compliance_metric PASSED [ 73%]
tests/unit/catalog/test_catalog_targets_and_metrics.py::test_cat57_026_repeated_evaluation_with_frozen_snapshot_is_deterministic PASSED [ 76%]
tests/unit/catalog/test_catalog_targets_and_metrics.py::test_cat57_027_evaluation_with_missing_data_reports_incomplete PASSED [ 79%]
tests/unit/catalog/test_catalog_targets_and_metrics.py::test_cat57_028_evaluation_run_persistence_and_retrieval PASSED [ 82%]
tests/unit/catalog/test_catalog_targets_and_metrics.py::test_cat57_029_evaluation_reports_never_expose_secret_values PASSED [ 85%]
tests/unit/catalog/test_catalog_targets_and_metrics.py::test_cat57_030_historical_evaluations_are_immutable PASSED [ 88%]
tests/unit/catalog/test_catalog_targets_api.py::test_api_unauthorized_access_blocked PASSED [ 91%]
tests/unit/catalog/test_catalog_targets_api.py::test_api_get_configured_targets PASSED [ 94%]
tests/unit/catalog/test_catalog_targets_api.py::test_api_run_and_retrieve_evaluation PASSED [ 97%]
tests/unit/catalog/test_catalog_targets_api.py::test_api_get_specific_views PASSED [100%]

============================= 34 passed in 17.80s =============================
```

### 2.2 Route Snapshot Verification
```
tests/security/test_routes_snapshot.py::test_openapi_routes_match_snapshot PASSED [ 50%]
tests/security/test_routes_snapshot.py::test_global_app_routes_match_snapshot_no_leak PASSED [100%]

============================== 2 passed in 7.83s ==============================
```

---

## 3. Environment & Verification Limitations (Rule 14 Statement)
- **Local Environment Execution:** Tests were executed in the Windows host environment using SQLite async engine (`sqlite+aiosqlite:///:memory:`).
- **PostgreSQL / Docker:** The local development host does not have a live Docker daemon or local PostgreSQL instance running. Full database integration and migration runs against PostgreSQL remain unverified locally and will be validated in GitHub Actions CI against PostgreSQL 16 container service.
- **Pilot State:** Real-world merchant partnerships and commercial feeds have not been connected; the catalog operates under controlled fixtures and pilot specifications. Real human evidence cards in `docs/evidence/` remain pending founder execution.
