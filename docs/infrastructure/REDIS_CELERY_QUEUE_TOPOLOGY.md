# Celery Task Queue Topology and Routing Specification

> **Worker architecture specification. Pre-pilot status maintained per AGENTS.md.**

---

## 1. Overview & Queue Hierarchy

FashXStudio leverages Celery with Redis broker and result backend. Tasks are distributed across 3 priority queues:

```
+-----------------------------------------------------------------------------------+
|                            Celery Worker Fleet                                    |
|                                                                                   |
|  +--------------------+    +--------------------+    +-------------------------+  |
|  |   TryOn Workers    |    |   Ingest Workers   |    |   Maintenance Workers   |  |
|  | (High Priority GPU)|    |   (Batch CPU)      |    |      (Scheduled CPU)    |  |
|  +---------+----------+    +---------+----------+    +------------+------------+  |
|            |                         |                            |               |
|  Polls     v               Polls     v                  Polls     v               |
|  +--------------------+    +--------------------+    +-------------------------+  |
|  |   queue: 'tryon'   |    |  queue: 'ingest'   |    |   queue: 'maintenance'  |  |
|  +--------------------+    +--------------------+    +-------------------------+  |
|            ^                         ^                            ^               |
|            |                         |                            |               |
|  Dispatches|               Dispatches|                  Dispatches|               |
|  +---------+-------------------------+----------------------------+------------+  |
|  |                         FastAPI Core Application & Celery Beat              |  |
|  +-----------------------------------------------------------------------------+  |
+-----------------------------------------------------------------------------------+
```

---

## 2. Queue Specifications

### A. `tryon` Queue (Real-Time Shopper Workload)
- **Primary Task**: `fashx.workers.app.process_tryon_job`
- **SLO**: Target job pickup < 2 seconds.
- **Worker Configuration**:
  - `worker_prefetch_multiplier = 1`: Prevents a single worker from prefetching and hoarding multiple tryon jobs while other workers remain idle.
  - `task_acks_late = True`: Task acknowledged only after successful result generation and storage upload.
  - `task_reject_on_worker_lost = True`: If an inference worker crashes or OOMs, the job is returned to the queue immediately.

### B. `ingest` Queue (Catalog & Garment Batch Processing)
- **Primary Tasks**:
  - `fashx.workers.app.ingest_catalog_feed`
  - `fashx.workers.app.enrich_garment_task`
- **SLO**: Batch processing completed within merchant SLA (e.g. < 4 hours).
- **Concurrency**: Autoscaled according to merchant catalog feed volume.

### C. `maintenance` Queue (System & Regulatory Cleanup)
- **Primary Tasks**:
  - `fashx.workers.app.relay_outbox_events` (Every 30 seconds via Beat)
  - `fashx.workers.app.sweep_storage_erasure` (Every 5 minutes via Beat - DPDP / GDPR)
  - `fashx.workers.app.run_retention_jobs` (Nightly at 00:00 UTC via Beat)
- **SLO**: Complete scheduled sweeps within cycle window.

---

## 3. Worker Launch Protocol

Workers must be launched targeting their explicit designated queues:

```bash
# Launch TryOn inference workers
celery -A fashx.workers.app worker -Q tryon -c 4 --loglevel=INFO

# Launch Ingestion batch workers
celery -A fashx.workers.app worker -Q ingest -c 8 --loglevel=INFO

# Launch Scheduled maintenance worker and Beat scheduler
celery -A fashx.workers.app worker -Q maintenance -B -c 2 --loglevel=INFO
```
