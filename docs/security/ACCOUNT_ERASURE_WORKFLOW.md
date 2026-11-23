# FashXStudio — Account Erasure & Biometric Deletion Workflow

## 1. Architectural Overview
The Account Erasure subsystem implements the **Right to Erasure ("Right to be Forgotten")** guaranteed under DPDP Act 2023 and GDPR Art. 17.
Erasure is designed as an all-or-nothing, fault-tolerant workflow executed across database records, in-memory caches, active authentication sessions, and private S3 object storage.

---

## 2. Erasure Lifecycle & State Transitions

```
[ Active User ] 
       │
       ▼ POST /api/v1/account/deletion-request
[ User Status: DELETION_PENDING ]
[ AccountDeletionJob: PENDING ]
       │
       ▼ Celery Worker `execute_account_deletion_job`
[ Stage 1: Immediate Biometric Erasure ]
  - Hard-delete from all BIOMETRIC_TABLES
  - Collect S3 storage keys and user prefix `u/{user_id}/`
  - Emit transactional OutboxMessage: StoragePurgeRequested
       │
       ▼ Stage 2: Event Log Anonymization
  - UPDATE domain_events SET user_id = NULL
  - UPDATE pilot_invites SET user_id = NULL
       │
       ▼ Stage 3: Account Hard-Deletion
  - Hard-delete from all ACCOUNT_TABLES (shopper_profiles, wardrobe, consent, etc.)
  - Hard-delete from CORE_AUTH (auth_identities, users)
       │
       ▼ Stage 4: Tombstone Insertion
  - INSERT INTO erasure_tombstones (user_id, erased_at)
       │
       ▼ Stage 5: Asynchronous Storage Purge
  - Delete S3 objects and purge prefix `u/{user_id}/`
  - Mark AccountDeletionJob: COMPLETED
```

---

## 3. Transactional Integrity & Isolation

1. **Savepoint Isolation (`SAVEPOINT`)**:
   - The erasure operation is executed inside a nested database savepoint (`session.begin_nested()`).
   - If any step fails during the multi-table deletion, the transaction rolls back cleanly to the savepoint without leaking partially erased data or corrupting the session.
2. **Anti-Resurrection Protection**:
   - On completion, `erasure_tombstones` records `(user_id, erased_at)`.
   - Any restore operation from point-in-time recovery (PITR) backups cross-references `erasure_tombstones` to purge resurrected records before serving production traffic.
3. **Session Invalidation**:
   - Immediate insertion of session revocation records into `revoked_auth_sessions` blocks any unexpired Cognito JWTs in transit.
   - Subsequent requests with previously issued tokens receive `401 Unauthorized`.
4. **Idempotent Worker Re-Execution**:
   - If the background worker fails or restarts mid-flight, jobs in `COMPLETED` state return `already_completed` immediately.
   - Retries adhere to exponential backoff with max 5 attempts before alerting on-call engineers via dead-letter queues.
