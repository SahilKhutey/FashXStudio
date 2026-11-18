# Connector Testing Standard (SA-001 through SA-025)

## 1. Quality Standards for Adapters

Every catalog connector in FashXStudio must be evaluated against the standard test criteria (SA-001 through SA-025) prior to production activation.

## 2. Test Requirements Matrix

| ID | Test Category | Specification | Test Implementation |
| :--- | :--- | :--- | :--- |
| **SA-001** | Contract Conformance | Adapter implements `CatalogSourceAdapterV2` protocol. | `test_adapter_contract.py` |
| **SA-002** | Auth Material | Generates valid headers for API Key, Bearer, Basic, Signed Request. | `test_source_auth.py` |
| **SA-003** | Token Caching | Caches OAuth tokens until 60s before expiry; single refresh on 401. | `test_source_auth.py` |
| **SA-004** | 403 Backoff | Blocks token refresh loops upon receiving HTTP 403 Forbidden. | `test_source_auth.py` |
| **SA-005** | Credential Masking | Credentials masked in logs, repr, and string representations. | `test_source_auth.py` |
| **SA-006** | Pagination State | Tracks cursors, page tokens, and total items accurately. | `test_source_pagination.py` |
| **SA-007** | Batch Sizing | Respects maximum batch size limits. | `test_source_pagination.py` |
| **SA-008** | Repeated Cursors | Bounded loop prevention: terminates on duplicate cursor cycle. | `test_source_pagination.py` |
| **SA-009** | Empty Pages | Terminate if 3 consecutive pages return 0 items with `has_more=True`. | `test_source_pagination.py` |
| **SA-010** | Rate Limiting | Token bucket throttling and dynamic `Retry-After` enforcement. | `test_source_rate_limiter.py` |
| **SA-011** | Bounded Retries | Max 3 attempts on 5xx and connection drops; exponential backoff. | `test_source_retry.py` |
| **SA-012** | Fail Fast | 400, 403, 404 fail immediately without retries. | `test_source_retry.py` |
| **SA-013** | Error Mapping | Maps exceptions to standard `SourceErrorCode` values. | `test_source_error_mapping.py` |
| **SA-014** | Checkpoint Safety | Products committed to database before checkpoint advances. | `test_checkpoint_safety.py` |
| **SA-015** | Incremental Delta | Advances watermark timestamp upon successful incremental run. | `test_incremental_and_full_sync.py` |
| **SA-016** | Full Snapshot | Exhaustive snapshot tracking for stale offer reconciliation. | `test_incremental_and_full_sync.py` |
| **SA-017** | Crash Recovery | Mid-run crash leaves checkpoint at last committed page. | `test_checkpoint_safety.py` |
| **SA-018** | Idempotency | Re-reading an already ingested page does not duplicate products. | `test_checkpoint_safety.py` |
| **SA-019** | Health Telemetry | Evaluates `HEALTHY`, `DEGRADED`, `AUTH_FAILED`, `RATE_LIMITED`, `STALE`. | `test_source_health.py` |
| **SA-020** | Fail Closed | Inactive or unapproved source denied by authorization guard. | `test_authorization_guard.py` |
| **SA-021** | Host Allowlist | Rejects URLs outside approved host allowlist. | `test_ssrf_and_security.py` |
| **SA-022** | SSRF Hardening | Loopback, private subnets, cloud metadata IPs strictly blocked. | `test_ssrf_and_security.py` |
| **SA-023** | Size Bounding | Responses exceeding 10MB streaming limit aborted. | `test_ssrf_and_security.py` |
| **SA-024** | Stale Safeguard | Failed or partial full-sync never marks offers out-of-stock. | `test_incremental_and_full_sync.py` |
| **SA-025** | Diagnostics Sanitization | Error traces and health reports sanitize credentials. | `test_source_auth.py` |
