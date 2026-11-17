# Dev Log: Phase 04.2 — User Account Lifecycle and Data Erasure

- **Date:** 2026-11-15
- **Branch:** `recovery/rc13.1-governance-correction`
- **Component:** User Lifecycle State Machine, Account Provisioning, Session Revocation, and DPDP/GDPR Erasure Worker

---

## 1. Context & Objectives
Phase 04.2 implements the complete shopper identity lifecycle, coordinating between Amazon Cognito User Pools (credentials and identity) and the FashXStudio backend/PostgreSQL (application profile, sessions, consent records, and storage erasure).

Key objectives:
1. Application account provisioning mapping Cognito `sub` to internal FashXStudio UUID.
2. Account lifecycle states: `PENDING_VERIFICATION`, `ACTIVE`, `DISABLED`, `DELETION_PENDING`, `DELETION_IN_PROGRESS`, `DELETED`.
3. Session registry supporting active session tracking, concurrent logins, and global revocation.
4. Self-service account disabling and asynchronous DPDP/GDPR-compliant data erasure worker.
5. Timing attack and user enumeration protections across account endpoints.
6. Execution and verification of lifecycle test cases.

---

## 2. Engineering Changes

### 2.1 Database Models & Alembic Migration
- Created `database/models/account.py` with declarative models:
  - `UserLifecycleHistory`: Audit trail of account status transitions.
  - `UserSession`: PostgreSQL-backed session registry tracking client devices and revocation timestamps.
  - `AccountDeletionJob`: Durable state machine managing S3 media purge and database records deletion.
- Extended `User` model with lifecycle columns: `status`, `email_normalized`, `email_verified`, `activated_at`, `disabled_at`, `deletion_requested_at`, `deleted_at`.
- Authored Alembic migration `0035_add_account_lifecycle_tables.py` revising `0034_add_revoked_auth_sessions.py`.

### 2.2 Account Repository & Service Layer
- Created `backend/fashx/account/repository.py`:
  - Atomic user provisioning with upsert on `(provider, provider_sub)`.
  - Session recording and global revocation logic.
  - Account deletion job queuing and status updates.
- Created `backend/fashx/account/service.py`:
  - Lifecycle state machine transitions with validation rules.
  - Enumeration-safe email normalization and lookups.
  - Self-service account disabling and deletion request handling.

### 2.3 Erasure Application Worker
- Created `backend/fashx/application/erasure.py`:
  - Coordinates multi-table cascading erasure (`ACCOUNT_TABLES`).
  - Purges private S3 objects (try-on references, garment photos, masks) and enqueues tombstone logs.
  - Supports idempotent re-execution on transient worker restarts.

### 2.4 API Router & Schemas
- Created `backend/fashx/account/router.py`:
  - `POST /api/v1/account/provision`: Idempotently creates or reconciles user.
  - `GET /api/v1/account/me`: Returns current account lifecycle status.
  - `POST /api/v1/account/email/change`: Validates and initiates email update flow.
  - `POST /api/v1/account/disable`: Disables account and revokes active sessions.
  - `POST /api/v1/account/delete`: Requests permanent erasure and queues deletion job.
  - `POST /api/v1/account/sessions/revoke-all`: Global revocation endpoint.

---

## 3. Verification & Test Execution

Command executed:
```bash
pytest tests/account/ -v
```

Command Output:
```
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.1.1, pluggy-1.6.0 -- C:\Users\ASUS\AppData\Local\Programs\Python\Python312\python.exe
hypothesis profile 'default'
rootdir: C:\Users\ASUS\Documents\FashXStudio
configfile: pytest.ini
plugins: anyio-4.12.1, hypothesis-6.156.6, langsmith-0.14.4, asyncio-1.4.0, cov-7.1.0
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collecting ... collected 14 items

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

============================= 14 passed in 5.27s ==============================
```
