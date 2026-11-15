# Phase 04.2 — User Account Lifecycle: Engineering Approval & Audit

## 1. Overview and Status
- **Phase Objective**: Implement and verify the complete shopper identity lifecycle for FashXStudio, from account registration through verification, authentication, session management, recovery, identity updates, account suspension, and permanent deletion.
- **Identity Provider**: Amazon Cognito User Pools (ap-south-1 Mumbai) + FashXStudio FastAPI Backend + PostgreSQL + Celery Deletion Worker.
- **Local Verification Status**: 🟢 Code complete and verified across 14/14 Account Lifecycle tests (`tests/account/`) and 105/105 Security tests (`tests/security/`).
- **Cloud Execution Status (Rule 14)**: Awaits human founder cloud execution against AWS Mumbai staging Cognito User Pool and RDS PostgreSQL.

---

## 2. Deliverables Register

| Deliverable ID | Component | Location | Description |
| :--- | :--- | :--- | :--- |
| **D04.2-01** | Account State Machine | `docs/security/ACCOUNT_STATE_MACHINE.md` | Formal 7-state machine: `PENDING_VERIFICATION`, `PROVISIONING`, `ACTIVE`, `DISABLED`, `DELETION_PENDING`, `DELETION_IN_PROGRESS`, `DELETED`. |
| **D04.2-02** | Lifecycle Specification | `docs/security/ACCOUNT_LIFECYCLE.md` | Detailed specification for tasks 4.2.1 through 4.2.12. |
| **D04.2-03** | Deletion Policy | `docs/security/ACCOUNT_DELETION_POLICY.md` | DPDP Act / GDPR data classification, cascading hard deletes, S3 purge, and resurrection prevention. |
| **D04.2-04** | Database Models | `database/models/identity.py`, `database/models/account.py` | Extended `User` with lifecycle status, `email_normalized`, `email_verified`, timestamps; `IdentityAccount`, `AuthSession`, `AccountDeletionJob`. |
| **D04.2-05** | Database Migration | `database/migrations/versions/0035_add_account_lifecycle_tables.py` | Linear Alembic migration adding columns, tables, foreign keys, and indexes. |
| **D04.2-06** | Backend Service & Router | `backend/fashx/account/` | FastAPI router mounted at `/api/v1/account`, `AccountService`, and `AccountRepository`. |
| **D04.2-07** | Durable Deletion Worker | `backend/fashx/workers/account_deletion.py` | Asynchronous worker processing `AccountDeletionJob` with S3 purging and fault-tolerant retry handling. |
| **D04.2-08** | Mobile Client Adapter | `mobile/src/auth/api/accountApi.ts` | TypeScript API client connecting Expo app to backend account endpoints. |
| **D04.2-09** | Test Suite | `tests/account/` | Comprehensive test suite covering state transitions, provisioning, API, workers, and concurrent sessions. |

---

## 3. Account Lifecycle Endpoints

| Endpoint | Method | Auth Required | Description |
| :--- | :--- | :--- | :--- |
| `/api/v1/account/provision` | `POST` | Bearer JWT | Idempotently provisions or reconciles internal `User` and `IdentityAccount` from verified Cognito token. |
| `/api/v1/account/me` | `GET` | Bearer JWT | Retrieves internal user profile, status, verification flag, roles, and timestamps. |
| `/api/v1/account/email-change` | `POST` | Bearer JWT | Initiates email change challenge for authenticated shopper. |
| `/api/v1/account/email-change/confirm` | `POST` | Bearer JWT | Confirms verification code and updates normalized email address. |
| `/api/v1/account/disable` | `POST` | Bearer JWT | Sets state to `DISABLED`, records `disabled_at`, and revokes all active sessions. |
| `/api/v1/account/deletion-request` | `POST` | Bearer JWT | Sets state to `DELETION_PENDING`, enqueues deletion job, revokes active sessions. |
| `/api/v1/account/deletion-status` | `GET` | Bearer JWT | Returns current execution status of account deletion job. |
| `/api/v1/account/sessions/revoke-all` | `POST` | Bearer JWT | Global logout: invalidates all active sessions for authenticated shopper. |

---

## 4. Verification and Rule 14 Disclosure

### Verified Locally
1. **Database Schema & Models**:
   - `alembic heads` verified single head `0035_add_account_lifecycle_tables`.
   - SQLite in-memory hermetic tests confirm table creation and foreign key constraints.
2. **Account Lifecycle Test Suite (`tests/account/`)**:
   - 14/14 tests passing.
3. **Security Test Suite (`tests/security/`)**:
   - 105/105 tests passing without regression.
4. **Route Surface Validation**:
   - `test_routes_snapshot.py` confirms exact route surface alignment across all 248 API routes.

### Pending Human Founder Execution on AWS (Rule 14)
- Local environment does not run live PostgreSQL or AWS ap-south-1 services.
- Real-world verification on staging AWS infrastructure requires:
  1. `alembic upgrade head; downgrade -1; upgrade head` against Amazon RDS PostgreSQL staging instance.
  2. Live Cognito User Pool registration and email code delivery in Mumbai region.
  3. Real S3 bucket prefix deletion execution on `fashx-staging-private-*`.
