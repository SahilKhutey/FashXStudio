# Merchant Operations Test Plan and Verification Matrix

## 1. Overview
This test plan validates the operational control plane for Phase 05.6. Verification covers unit domain logic, API contracts, security boundaries, tenant isolation, and regression verification across all catalog operations.

---

## 2. Test Verification Matrix (OPS-001 through OPS-042)

| Test ID | Domain / Functionality | Description | Target Component | Status |
| :--- | :--- | :--- | :--- | :--- |
| **OPS-001** | Source Connection | Register valid merchant API source, check default state & schedule | `SourceConnectionService` | 🟢 Verified |
| **OPS-002** | Source Connection | Rejection of duplicate source slug with `source_slug_conflict` | `SourceConnectionService` | 🟢 Verified |
| **OPS-003** | Source Connection | Rejection of non-existent merchant with `merchant_not_found` | `SourceConnectionService` | 🟢 Verified |
| **OPS-004** | Security / Vault | Credential masking utility scrubs keys/URIs/ARNs | `mask_credential_reference` | 🟢 Verified |
| **OPS-005** | Schedule Creation | Default schedule created with interval >= 15 min | `SourceConnectionService` | 🟢 Verified |
| **OPS-006** | Source Lifecycle | Disabling source sets `is_enabled=False` & pauses schedule | `SourceLifecycleService` | 🟢 Verified |
| **OPS-007** | Source Lifecycle | Disabling source aborts active running/queued IngestRuns | `SourceLifecycleService` | 🟢 Verified |
| **OPS-008** | Source Lifecycle | Cannot enable source when authorization is `REVOKED` or `SUSPENDED` | `SourceLifecycleService` | 🟢 Verified |
| **OPS-009** | Source Lifecycle | Audit event `SOURCE_STATUS_CHANGED` logged with reason | `SourceLifecycleService` | 🟢 Verified |
| **OPS-010** | Source Lifecycle | Pausing source keeps schedule paused | `SourceLifecycleService` | 🟢 Verified |
| **OPS-011** | Manual Sync | Manual sync trigger enqueues IngestRun in `queued` state | `ManualSyncService` | 🟢 Verified |
| **OPS-012** | Manual Sync | Idempotency key deduplication returns existing run (`is_duplicate_request=True`) | `ManualSyncService` | 🟢 Verified |
| **OPS-013** | Manual Sync | Reject sync trigger if source is disabled (`source_disabled`) | `ManualSyncService` | 🟢 Verified |
| **OPS-014** | Manual Sync | Reject sync trigger if source authorization is revoked | `ManualSyncService` | 🟢 Verified |
| **OPS-015** | Manual Sync | Reject concurrent sync unless `force=True` | `ManualSyncService` | 🟢 Verified |
| **OPS-016** | Schedule Service | Configure cadence with interval >= 15 min & timezone | `SyncScheduleService` | 🟢 Verified |
| **OPS-017** | Schedule Service | Reject interval < 15 min with `invalid_interval` | `SyncScheduleService` | 🟢 Verified |
| **OPS-018** | Schedule Service | Reject invalid timezone with `invalid_timezone` | `SyncScheduleService` | 🟢 Verified |
| **OPS-019** | Schedule Service | Due schedule detection advances `next_run_at` | `SyncScheduleService` | 🟢 Verified |
| **OPS-020** | Schedule Service | Disabled sources excluded from due schedules queue | `SyncScheduleService` | 🟢 Verified |
| **OPS-021** | Status Dashboard | Aggregates duration, counts, last status, and health flag | `SyncStatusService` | 🟢 Verified |
| **OPS-022** | Status Dashboard | Accurate duration calculation from finished/started timestamps | `SyncStatusService` | 🟢 Verified |
| **OPS-023** | Status Dashboard | Health evaluates False when last run failed | `SyncStatusService` | 🟢 Verified |
| **OPS-024** | Error Reporting | Logs structured error in `ingest_run_errors` table | `IngestionReportService` | 🟢 Verified |
| **OPS-025** | Error Reporting | Sensitive token and API key redaction (`redact_sensitive_error_message`) | `IngestionReportService` | 🟢 Verified |
| **OPS-026** | Error Reporting | Query errors with pagination and run_id filtering | `IngestionReportService` | 🟢 Verified |
| **OPS-027** | Error Reporting | Preserves retryable flag and error category | `IngestionReportService` | 🟢 Verified |
| **OPS-028** | Quarantine Report | Queries quarantined products from `catalog_ingestion_quarantine` | `RejectionReportService` | 🟢 Verified |
| **OPS-029** | Quarantine Report | Automated resolution guidance generation | `RejectionReportService` | 🟢 Verified |
| **OPS-030** | Quarantine Report | Filtering quarantine by status (`PENDING`, `RESOLVED`) | `RejectionReportService` | 🟢 Verified |
| **OPS-031** | Image Dashboard | Multi-operation image rights evaluation (fetch, store, display, AI, VTO) | `ImagePermissionStatusService`| 🟢 Verified |
| **OPS-032** | Image Dashboard | Queries asset counts (total, active, suspended) | `ImagePermissionStatusService`| 🟢 Verified |
| **OPS-033** | Image Dashboard | Emits warnings when display or VTO permissions are missing | `ImagePermissionStatusService`| 🟢 Verified |
| **OPS-034** | Takedown Workflow | Admin takedown suspends source & schedule immediately | `SourceTakedownService` | 🟢 Verified |
| **OPS-035** | Takedown Workflow | Cancels active jobs & deactivates all merchant offers | `SourceTakedownService` | 🟢 Verified |
| **OPS-036** | Takedown Workflow | Purges/suspends image assets and records immutable audit event | `SourceTakedownService` | 🟢 Verified |
| **OPS-037** | Product Overrides | Persists overrides for allowed fields (`title`, `price_minor`) | `MerchantProductUpdateService`| 🟢 Verified |
| **OPS-038** | Product Overrides | Rejects overrides of source-managed fields (`source_product_id`, etc.) | `MerchantProductUpdateService`| 🟢 Verified |
| **OPS-039** | Product Removal | Deactivation of offer preserves shared canonical garment if other offers exist | `MerchantProductRemovalService`| 🟢 Verified |
| **OPS-040** | Product Removal | Deactivation of sole remaining offer marks canonical garment inactive | `MerchantProductRemovalService`| 🟢 Verified |
| **OPS-041** | Tenant Isolation | Prevents cross-merchant source/offer modifications | `SourceLifecycleService` | 🟢 Verified |
| **OPS-042** | Audit Trail | Immutable operational audit logging and tenant-scoped retrieval | `SourceAuditService` | 🟢 Verified |

---

## 3. Test Execution Summary
- **Unit Suite (`tests/unit/catalog/test_merchant_catalog_operations.py`)**: 24/24 Passed.
- **API Integration Suite (`tests/unit/catalog/test_merchant_catalog_operations_api.py`)**: 6/6 Passed.
- **Full Catalog Test Suite (`tests/unit/catalog/`)**: 143/143 Passed.
- **OpenAPI Route Snapshot Suite (`tests/security/test_routes_snapshot.py`)**: 2/2 Passed.
