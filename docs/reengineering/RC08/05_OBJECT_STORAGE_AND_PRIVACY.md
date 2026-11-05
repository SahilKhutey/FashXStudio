# RC08 — Object Storage, Privacy & Cascading Erasure

## 1. Storage Topology
- **Buckets**: Staging (`fashx-staging-media`) and Production (`fashx-prod-media`).
- **Access Level**: Private only (`BlockPublicAccess=true`, `SSE-S3` AES-256 server-side encryption enabled).
- **Access Pattern**: Pre-signed URLs with maximum TTL of 300 seconds (5 minutes) generated on demand for authenticated users.

## 2. Privacy Architecture: Cascading Erasure
Under the DPDP Act and GDPR, account deletion must purge all associated personal data from both database and object storage:

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant API as FastAPI Gateway
    participant DB as PostgreSQL
    participant Queue as Redis / Celery
    participant S3 as Object Storage (S3/R2)

    User->>API: DELETE /api/v1/me (Consent Withdrawal / Account Erasure)
    API->>DB: Begin Transaction
    API->>DB: Mark Account Status = "pending_deletion"
    API->>DB: Extract Object Keys (photos, tryon results)
    API->>Queue: Enqueue ErasureJob(user_id, [keys])
    API->>DB: Delete User, Profile, Consents, Wardrobe, FeedSignals
    API->>DB: Commit Transaction
    API-->>User: 204 No Content

    Queue->>S3: Batch Delete Objects (user photos, tryon results)
    alt Transient S3 Failure
        Queue->>Queue: Retry with exponential backoff (max 5 attempts)
    else Success
        Queue->>DB: Record Minimal Audit Token (sha256(user_id), erased_at)
    end
```

## 3. Strict Erasure Rules
1. **No Phantom Artifacts**: A successful database deletion must not be considered complete until all referenced S3 objects have been deleted.
2. **Retryable Ledger**: Any object-deletion failure is queued for immediate background retry. If unrecoverable after 5 attempts, an alert is triggered.
3. **Audit Token**: Only a cryptographic one-way hash (`sha256(user_id)`) with deletion timestamp is preserved for compliance proof. All personal identifiers are permanently eliminated.
