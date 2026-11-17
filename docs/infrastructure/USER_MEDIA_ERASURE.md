# FashXStudio — User Media Erasure Workflow (Phase 03.4)

## 1. Principles
User profile photographs, uploaded body images, and generated virtual try-on renders are sensitive personal data. When a user deletes their account or exercises privacy erasure rights:
1. Deletion must be **durable and guaranteed** against transient network or storage failures.
2. Deletion must be **idempotent** (safe to retry multiple times without error).
3. Erasure cannot be marked complete in PostgreSQL until S3 returns HTTP 404 / NoSuchKey on verification.

---

## 2. Multi-Step Erasure Sequence
```mermaid
sequenceDiagram
    participant User as Authenticated User
    participant API as FastAPI /application/erasure
    participant DB as PostgreSQL Database
    participant Worker as Outbox Worker
    participant S3 as Amazon S3

    User->>API: POST /api/v1/profile/erase
    API->>API: Verify user authentication & consent record
    API->>DB: Record deletion intent in outbox_messages (topic: 'media.erasure')
    API->>DB: Mark user & media status as 'deleting'
    API-->>User: 202 Accepted (Erasure initiated)

    Note over Worker: Asynchronous Outbox Worker execution
    Worker->>DB: Claim pending outbox_messages
    Worker->>S3: DeleteObject (original user upload)
    Worker->>S3: DeleteObject (VTO intermediate artifacts)
    Worker->>S3: DeleteObject (VTO render outputs)
    Worker->>S3: HeadObject verification on each key
    S3-->>Worker: 404 NoSuchKey (confirmed purged)
    Worker->>DB: Mark media records as 'deleted' (deleted_at = NOW())
    Worker->>DB: Mark outbox message published
```

---

## 3. Deletion Verification Probe
Implemented in `backend/fashx/infrastructure/storage/deletion.py`:
- `delete_object(key)` sends `DeleteObject` command to S3.
- `object_exists(key)` issues `HeadObject`. It returns `False` if `status == 404` or error code is `NoSuchKey` / `NotFound`.
- If an authorization error (`403 AccessDenied`) or server failure occurs during probe, the exception is re-raised and the outbox worker retries with exponential backoff.
