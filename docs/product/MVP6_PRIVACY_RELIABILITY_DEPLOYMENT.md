# MVP 6: Privacy, Reliability & Deployment Verification

## Implementation Overview

MVP 6 establishes production-grade hardening, fail-fast configuration validation, background worker execution, reliable transactional outbox processing, privacy-compliant account erasure, scheduled data retention, dependency readiness checks, and deployment runbooks.

---

### Key Changes

1. **Canonical Production Fail-Fast Validation**:
   - Fixed the production bypass vulnerability in `backend/fashx/core/settings.py` where production checks were previously gated only on `ENV=prod`.
   - Unified validation under `self.is_production` (`app_env.lower() in ("production", "prod") or self.env == "prod"`).
   - Enforces that `self.env == "prod"` when production mode is activated, rejecting inconsistent environment flags.
   - Strictly enforces production invariants:
     - Requires `REPO_BACKEND=sql` (rejecting `memory`).
     - Requires `STORAGE_BACKEND=s3` with configured private bucket and IAM role or keys (rejecting `local`).
     - Requires `AUTH_MODE=jwks` with `AUTH_JWKS_URL` (rejecting `local`).
     - Forbids `TRYON_PROVIDER=mock` (rule I08).
     - Forbids `TRYON_PROVIDER=fashn_selfhost` until a verified non-mock adapter is implemented.
     - Forbids wildcard CORS origins (`*`).
     - Forbids `ENABLE_B2B=True` for this MVP release.
     - Requires valid `PRIVACY_URL` and `TERMS_URL`.
   - Updated `.env.example` with documented Development Defaults and a Production Profile Reference.

2. **Adapter Factory Verification**:
   - In `backend/fashx/core/dependencies.py`, updated `get_tryon_adapter()` so that `TRYON_PROVIDER=fashn_selfhost` raises `NotImplementedError` rather than silently falling back to `MockAdapter`.

3. **Real Background Worker Task Execution**:
   - In `backend/fashx/workers/app.py`, replaced placeholder tasks with actual domain operations:
     - `process_tryon_job`: bootstraps units of work, executes `ProcessTryOnJobUseCase`, and handles bounded exponential retries on transient errors.
     - `ingest_catalog_feed`: queries `CatalogUnitOfWork`, verifies source existence, and validates source clearance status (`cleared`).
     - `enrich_garment_task`: invokes `EnrichGarmentUseCase` with `CatalogUnitOfWork`, incrementing garment version and persisting attributes.
     - `relay_outbox_events`: invokes `run_outbox_worker_once`, processing pending outbox events (storage deletions, purges).
     - `sweep_storage_erasure`: executes retry sweep for storage purge events via the transactional outbox.
     - `run_retention_jobs`: executes `run_daily_retention`, pruning unsaved try-ons (>30 days), deleting stale impressions (>90 days), and anonymizing analytics (>365 days).
   - Created safe synchronous executor helper `_run_sync` ensuring async coroutines run cleanly within Celery worker threads.

4. **Account Erasure & Data Retention**:
   - Verified `erase_account` in `backend/fashx/application/erasure.py`: cascades hard deletion of biometric records, purges account rows, writes immutable tombstones, and schedules storage prefix purges via the transactional outbox.
   - Enforced multi-stage consent validation before reading user photos and before submitting requests to inference providers.

5. **Operational Health & Dependency Readiness**:
   - Verified `/health/ready` and `/healthz/ready` in `backend/fashx/health/router.py`: evaluates live PostgreSQL, Redis, and JWKS connectivity without leaking connection strings, tokens, or network topology. Returns HTTP 503 degraded when a required dependency fails.

6. **CI/CD Release Policies**:
   - Frozen post-MVP commerce domains (`C05-C11`) are unmounted by default (`FASHX_ENABLE_FROZEN=0`) in production configurations, isolating them from blocking MVP releases.
   - Security scanning (`bandit`) and dependency audit (`pip-audit`) policies are documented with clear exception tracking.

---

## Automated Test Verification

Command:
```powershell
python -c "import pytest; print(pytest.main(['tests/unit/test_mvp6_privacy_reliability_deployment.py', 'tests/unit/test_settings.py', 'tests/unit/test_settings_prod_refusal.py', 'tests/unit/test_retention.py', 'tests/unit/test_tryon_adapters.py', 'tests/unit/test_mvp5_closet_shopping_journey.py', '-v']))"
```

Output:
```
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.1.1, pluggy-1.6.0 -- C:\Users\ASUS\AppData\Local\Programs\Python\Python312\python.exe
hypothesis profile 'default'
rootdir: C:\Users\ASUS\Documents\FashXStudio
configfile: pytest.ini
plugins: anyio-4.12.1, hypothesis-6.156.6, langsmith-0.14.4, asyncio-1.4.0, cov-7.1.0
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collecting ... collected 39 items

tests/unit/test_mvp6_privacy_reliability_deployment.py::test_settings_fail_fast_canonical_production PASSED [  2%]
tests/unit/test_mvp6_privacy_reliability_deployment.py::test_tryon_adapter_resolution_refuses_unimplemented_selfhost PASSED [  5%]
tests/unit/test_mvp6_privacy_reliability_deployment.py::test_worker_tryon_job_retry_on_transient_error PASSED [  7%]
tests/unit/test_mvp6_privacy_reliability_deployment.py::test_worker_ingest_feed_verifies_source_cleared PASSED [ 10%]
tests/unit/test_mvp6_privacy_reliability_deployment.py::test_worker_enrich_garment_task_execution PASSED [ 12%]
tests/unit/test_mvp6_privacy_reliability_deployment.py::test_worker_outbox_relay_and_erasure_sweeps PASSED [ 15%]
tests/unit/test_mvp6_privacy_reliability_deployment.py::test_worker_retention_job_execution PASSED [ 17%]
tests/unit/test_mvp6_privacy_reliability_deployment.py::test_readiness_reports_503_on_dependency_failure PASSED [ 20%]
tests/unit/test_mvp6_privacy_reliability_deployment.py::test_account_erasure_workflow PASSED [ 23%]
tests/unit/test_mvp6_privacy_reliability_deployment.py::test_cross_user_isolation_blocks_unauthorized_access PASSED [ 25%]
tests/unit/test_settings.py::test_production_settings_flag PASSED        [ 28%]
tests/unit/test_settings.py::test_production_requires_env_prod PASSED    [ 30%]
tests/unit/test_settings.py::test_development_defaults PASSED            [ 33%]
tests/unit/test_settings_prod_refusal.py::test_prod_accepts_valid_production_config PASSED [ 35%]
tests/unit/test_settings_prod_refusal.py::test_prod_refuses_memory_repo PASSED [ 38%]
tests/unit/test_settings_prod_refusal.py::test_prod_refuses_local_storage PASSED [ 41%]
tests/unit/test_settings_prod_refusal.py::test_prod_refuses_missing_s3_bucket PASSED [ 43%]
tests/unit/test_settings_prod_refusal.py::test_prod_refuses_local_auth_mode PASSED [ 46%]
tests/unit/test_settings_prod_refusal.py::test_prod_refuses_mock_tryon_provider PASSED [ 48%]
tests/unit/test_settings_prod_refusal.py::test_prod_refuses_wildcard_cors PASSED [ 51%]
tests/unit/test_retention.py::test_cleanup_unsaved_tryons_purges_storage_and_records PASSED [ 53%]
tests/unit/test_retention.py::test_cleanup_impressions_deletes_older_than_cutoff PASSED [ 56%]
tests/unit/test_retention.py::test_anonymize_analytics_strips_user_id PASSED [ 58%]
tests/unit/test_retention.py::test_run_daily_retention_orchestration PASSED [ 61%]
tests/unit/test_tryon_adapters.py::test_mock_tryon_adapter_execution PASSED [ 64%]
tests/unit/test_tryon_adapters.py::test_fashn_api_adapter_license_guard PASSED [ 66%]
tests/unit/test_tryon_adapters.py::test_fashn_api_adapter_conforms_to_contract PASSED [ 69%]
tests/unit/test_tryon_adapters.py::test_get_tryon_adapter_fail_closed_without_key PASSED [ 71%]
tests/unit/test_tryon_adapters.py::test_fashn_api_submit_collect_mock_transport PASSED [ 74%]
tests/unit/test_tryon_adapters.py::test_fashn_api_error_mappings_and_ssrf_guard PASSED [ 76%]
tests/unit/test_tryon_adapters.py::test_process_job_use_case_dynamic_adapter_resolution PASSED [ 79%]
tests/unit/test_mvp5_closet_shopping_journey.py::test_wardrobe_save_derives_user_from_principal PASSED [ 82%]
tests/unit/test_mvp5_closet_shopping_journey.py::test_wardrobe_save_rejects_user_id_mismatch PASSED [ 84%]
tests/unit/test_mvp5_closet_shopping_journey.py::test_wardrobe_save_idempotency_and_uniqueness PASSED [ 87%]
tests/unit/test_mvp5_closet_shopping_journey.py::test_list_my_wardrobe_endpoint PASSED [ 89%]
tests/unit/test_mvp5_closet_shopping_journey.py::test_remove_from_wardrobe_ownership_enforcement PASSED [ 92%]
tests/unit/test_mvp5_closet_shopping_journey.py::test_retailer_url_validation PASSED [ 94%]
tests/unit/test_mvp5_closet_shopping_journey.py::test_buy_click_validates_garment_offer_relationship PASSED [ 97%]
tests/unit/test_mvp5_closet_shopping_journey.py::test_tryon_history_lists_user_jobs_with_signed_urls PASSED [100%]

============================= 39 passed in 22.72s =============================
0
```

---

## Environment & Gate Compliance Note

- Unit tests and configuration tests executed and passed hermetically with SQLite test fixtures.
- In accordance with repository Rule 14, Docker and a local PostgreSQL daemon on localhost:5432 are not active in this development environment; execution of `scripts/ci/local_gate.sh` and full database migrations against PostgreSQL will run in the GitHub Actions CI pipeline.
