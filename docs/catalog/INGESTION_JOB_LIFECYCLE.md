# Ingestion Job Lifecycle

## 1. Lifecycle States

Every catalog ingestion execution is tracked in PostgreSQL via `IngestRun` with the following lifecycle states:

```mermaid
stateDiagram-v2
    [*] --> QUEUED: Scheduled / Triggered
    QUEUED --> VALIDATING: Check Source Permissions
    VALIDATING --> RUNNING: Authorization Cleared
    VALIDATING --> REJECTED: Unregistered / Suspended / Revoked
    RUNNING --> COMPLETED: 100% Records Processed
    RUNNING --> PARTIAL: Partial Success (Quarantine > 0)
    RUNNING --> REJECTED: All Records Quarantined
    RUNNING --> FAILED: System / DB Error
    RUNNING --> ABORTED: Admin Cancel / Emergency Takedown
```

---

## 2. IngestRun Schema Extensions

In Alembic migration `0040_add_catalog_ingestion_quarantine.py`, `IngestRun` was enhanced with:
- `merchant_id`: Direct relational link to the owning merchant.
- `sync_mode`: `'full'`, `'incremental'`, or `'batch'`.
- `correlation_id`: Distributed tracing UUID matching upstream caller context.
- `counts`: Structured JSON metrics dictionary (`total`, `validated`, `inserted`, `updated`, `unchanged`, `rejected`, `quarantined`).
