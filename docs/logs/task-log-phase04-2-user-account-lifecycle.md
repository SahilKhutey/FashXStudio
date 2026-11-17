# Task Log: Phase 04.2 — User Account Lifecycle and Data Erasure

- **Date:** 2026-11-15
- **Branch:** `recovery/rc13.1-governance-correction`
- **Execution Target:** Workstream 4.2 Account Lifecycle, Session Registry & Erasure Worker

---

## Task Progress Checklist

- [x] **4.2.1 Application Account Data Model**: Created `database/models/account.py` (`UserLifecycleHistory`, `UserSession`, `AccountDeletionJob`) and updated `User` model.
- [x] **4.2.2 Alembic Migration**: Authored and tested migration `0035_add_account_lifecycle_tables.py` with foreign keys and check constraints.
- [x] **4.2.3 Idempotent Provisioning Engine**: Implemented `POST /api/v1/account/provision` linking external Cognito `sub` to internal user ID.
- [x] **4.2.4 Lifecycle State Machine**: Implemented state transitions across `PENDING_VERIFICATION`, `ACTIVE`, `DISABLED`, `DELETION_PENDING`, `DELETED`.
- [x] **4.2.5 Session Registry**: Implemented PostgreSQL-backed session recording with user-agent, IP hash, and revocation timestamps.
- [x] **4.2.6 Global Session Revocation**: Implemented `POST /api/v1/account/sessions/revoke-all` revoking all active refresh and access tokens.
- [x] **4.2.7 Self-Service Account Disabling**: Implemented `POST /api/v1/account/disable` immediately revoking credentials and blocking profile access.
- [x] **4.2.8 Permanent Deletion Request**: Implemented `POST /api/v1/account/delete` entering grace period and creating durable deletion job.
- [x] **4.2.9 Background Erasure Worker**: Built `backend/fashx/application/erasure.py` purging S3 objects and cascading database records across all account tables.
- [x] **4.2.10 User Enumeration Defense**: Validated timing consistency across email normalization and account endpoints.
- [x] **4.2.11 Mobile Client API**: Implemented mobile API client wrappers in `mobile/src/auth/api/accountApi.ts`.
- [x] **4.2.12 Test Suite Execution**: Authored and executed 14 unit and integration tests under `tests/account/` (14/14 passed in 5.27s).

---

## Test Verification Output Log

```text
tests/account/test_account_api.py::test_unauthenticated_account_endpoints_return_401 PASSED [  7%]
tests/account/test_account_api.py::test_provision_and_get_me_flow PASSED [ 14%]
tests/account/test_account_api.py::test_email_change_workflow PASSED     [ 21%]
tests/account/test_account_api.py::test_disable_account_flow PASSED      [ 28%]
tests/account/test_account_api.py::test_revoke_all_sessions_endpoint PASSED [ 35%]
tests/account/test_account_deletion_worker.py::test_account_deletion_worker_full_lifecycle PASSED [ 42%]
tests/account/test_account_deletion_worker.py::test_account_deletion_worker_idempotent_reexecution PASSED [ 50%]
tests/account/test_account_provisioning.py::test_idempotent_account_provisioning PASSED [ 57%]
tests/account/test_account_provisioning.py::test_unverified_provisioning_and_reconciliation PASSED [ 64%]
tests/account/test_concurrent_sessions.py::test_concurrent_sessions_recording_and_revocation PASSED [ 71%]
tests/account/test_enumeration_protections.py::test_enumeration_protection_timing_consistency PASSED [ 78%]
tests/account/test_lifecycle_state_machine.py::test_account_status_enum_values PASSED [ 85%]
tests/account/test_lifecycle_state_machine.py::test_user_model_defaults PASSED [ 92%]
tests/account/test_lifecycle_state_machine.py::test_user_state_transitions PASSED [100%]
```
