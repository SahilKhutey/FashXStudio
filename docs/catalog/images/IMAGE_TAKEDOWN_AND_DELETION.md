# Image Takedown and Deletion Runbook

## 1. Takedown Workflow Sequence

Image takedown is an integrated legal, security, and object lifecycle workflow:

```mermaid
sequenceDiagram
    autonumber
    actor Admin as Merchant / Legal / Admin
    participant API as Admin Takedowns API
    participant Life as ImageLifecycleService
    participant DB as PostgreSQL
    participant S3 as Amazon S3

    Admin->>API: POST /api/v1/admin/catalog/images/takedowns
    API->>Life: initiate_takedown(scope, reason)
    Life->>DB: Create catalog_image_takedowns (STATUS: RECEIVED)
    Life->>DB: Set assets STATUS = SUSPENDED
    Life->>DB: Enqueue deletion jobs (ORIGINAL, DERIVATIVES)
    Life->>S3: Delete S3 objects across keys
    S3-->>Life: Confirm object deletion
    Life->>DB: Mark deletion jobs COMPLETED
    Life->>DB: Set assets STATUS = DELETED
    Life->>DB: Set takedown STATUS = COMPLETED
    Life-->>API: Return ImageTakedownResponse
    API-->>Admin: Confirmed Takedown
```

---

## 2. Durability & Retry Invariants

1. **Immediate Suspension**: Upon receipt of a takedown, assets are set to `SUSPENDED` immediately, blocking subsequent pre-signed URL generation and AI processing before deletions finish.
2. **Per-Object Audit**: Deletions are tracked per target key in `catalog_image_deletion_jobs`.
3. **Partial Failure Resilience**: If an S3 delete call fails, the job remains `FAILED` with incremented retry count, and takedown status remains `PROCESSING` until confirmed.
