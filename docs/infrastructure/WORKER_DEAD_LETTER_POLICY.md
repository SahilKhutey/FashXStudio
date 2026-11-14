# FashXStudio — Worker Dead-Letter Handling Policy (Phase 03.3)

## 1. Overview
Redis is an in-memory ephemeral queue broker and does not provide built-in durable dead-letter storage. To guarantee zero message loss when background tasks exhaust their retry budgets or encounter non-retryable errors, FashXStudio records failed tasks durably into **PostgreSQL** in table `worker_dead_letters`.

---

## 2. Database Schema
Defined in migration `0033_add_worker_dead_letters.py` and model `WorkerDeadLetter` (`database/models/operations.py`):

```sql
CREATE TABLE worker_dead_letters (
    id UUID PRIMARY KEY,
    task_id VARCHAR(255) NOT NULL UNIQUE,
    task_name VARCHAR(255) NOT NULL,
    queue_name VARCHAR(100) NOT NULL,
    error_type VARCHAR(255) NOT NULL,
    error_message VARCHAR(1000) NOT NULL,
    safe_payload JSON NOT NULL DEFAULT '{}',
    status VARCHAR(30) NOT NULL DEFAULT 'pending',
    attempts INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    resolved_at TIMESTAMP WITH TIME ZONE
);

CREATE UNIQUE INDEX ix_worker_dead_letters_task_id ON worker_dead_letters (task_id);
CREATE INDEX ix_worker_dead_letters_status ON worker_dead_letters (status);
CREATE INDEX ix_worker_dead_letters_created_at ON worker_dead_letters (created_at);
```

---

## 3. Privacy & Sanitization Boundary
Under **no circumstances** should user biometric measurements, body photos, pre-signed S3 download URLs, or authorization tokens be persisted in dead-letter records.

The `build_safe_payload` function in `backend/fashx/workers/dead_letter.py` enforces strict filtering:
- `fashx.workers.app.process_tryon_job`: persists only `{"job_id": "<uuid>"}`.
- `fashx.workers.app.ingest_catalog_feed`: persists only `{"source_id": "<uuid>"}`.
- `fashx.workers.app.enrich_garment_task`: persists only `{"garment_id": "<uuid>"}`.
- Any payload containing `Bearer`, `s3://`, `http://`, or `https://` is rejected.
- Unregistered tasks persist `{}`.

---

## 4. Failure Callback Flow
Every Celery task inherits from `FashxTask`. When an execution fails permanently:
1. `on_failure` callback triggers.
2. Extracts `task_id`, `task_name`, `routing_key`, error type, and sanitized payload.
3. Synchronously executes `_persist_dead_letter_async` via `_run_sync`.
4. Upserts record into `worker_dead_letters` (`ON CONFLICT (task_id)`).
5. If the database write fails, the error is logged as critical without raising an exception that crashes the worker process.

---

## 5. Operator Triage & Replay Protocol
1. **Inspection**:
   ```sql
   SELECT id, task_name, queue_name, error_type, attempts, created_at 
   FROM worker_dead_letters 
   WHERE status = 'pending' 
   ORDER BY created_at DESC;
   ```
2. **Replay**:
   After resolving upstream service outages or bugs, an operator can replay dead-letter jobs using their `safe_payload` identifiers:
   ```python
   # Example replay for a failed tryon job:
   from fashx.workers.app import process_tryon_job
   process_tryon_job.delay("f7b5a88c-7f55-46aa-bd47-19bf2e32f170")
   ```
3. **Resolution**:
   ```sql
   UPDATE worker_dead_letters 
   SET status = 'resolved', resolved_at = NOW() 
   WHERE id = '<dead_letter_uuid>';
   ```
