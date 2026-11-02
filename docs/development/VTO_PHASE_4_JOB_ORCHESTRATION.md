# VTO Phase 4 — Try-On Job Orchestration, Input Assembly, and Asynchronous Processing

**Project:** FashXStudio
**Phase:** VTO-4
**Status:** Implementation specification
**Objective:** Assemble prepared garment assets (Phase 2) and user portrait assets (Phase 3) into an asynchronous, persistent, database-backed virtual try-on queue with worker claiming, lease renewal, cancellation, idempotency, and status polling.

## 1. Scope
Phase 4 implements the orchestration and asynchronous execution layer connecting user inputs to the try-on inference engine without blocking synchronous API requests.

Included:
- Canonical job creation service (`CreateTryOnJobUseCase`) validating user, consent (`body_photo`), portrait photo ownership, and garment VTO eligibility (`tryon_supported`, category checks).
- Deterministic composite cache key generation (`compute_tryon_cache_key`) incorporating model version, pipeline version, configuration hash, user photo version/SHA-256, and garment version.
- Instant cache reuse: if an artifact exists for the cache key and consent is valid, return cached completed result immediately.
- Client idempotency enforcement via `(user_id, idempotency_key)` unique constraint.
- Database-backed asynchronous queue using PostgreSQL `SKIP LOCKED` (SQLite fallback for tests).
- Worker lease protocol: atomic claim (`claim_next_job`), heartbeat lease renewal (`renew_lease`), and release (`release_lease`).
- Safe recovery of abandoned/stale jobs whose lease expired without completion.
- Two-tier cancellation protocol: immediate transition to `cancelled` for queued jobs; cooperative cancellation flag (`cancel_requested=True`) for running jobs.
- API endpoints:
  - `POST /api/v1/tryon/jobs` — Enqueue try-on job (202 Accepted) or return cached result.
  - `GET /api/v1/tryon/jobs/{job_id}` — Status polling with owner validation.
  - `POST /api/v1/tryon/jobs/{job_id}/cancel` — Cancel queued or running job.
  - `GET /api/v1/tryon/jobs/{job_id}/result` — Ephemeral signed download URL (409 Conflict if not completed).
- Two-phase provider retry resilience: preserves `provider_job_id` during retryable provider timeouts so long-running inference jobs are not duplicated.
- Version capture: `TryOnArtifact` records `photo_version` and `garment_version` from job inputs.

Excluded:
- Live commercial GPU inference execution (Phase 5).
- Multi-garment layered styling (Phase 6).
- Garment sizing recommendations (Phase 7).

## 2. Architecture & State Machine

```
                   +-------------------+
                   |   User Submits    |
                   |   POST /jobs      |
                   +---------+---------+
                             |
                   [Cache Hit Check]
                    /             \
             (Hit) /               \ (Miss)
                  v                 v
          +---------------+  +---------------+
          | Return Cached |  | Status: Queued|
          | 200/202 Result|  +-------+-------+
          +---------------+          |
                                     | Worker Claims
                                     | (sets locked_by, locked_at)
                                     v
                             +---------------+
                             |Status: Running|
                             +-------+-------+
                                     |
               +---------------------+---------------------+
               |                     |                     |
               v                     v                     v
       [Pre-processing]        [Inference]          [Cancel Signal]
               |                     |                     |
               v                     v                     v
       +---------------+     +---------------+     +---------------+
       | C2PA / Water- |     | Quality Check |     | Status:       |
       | marking       |     | (Luminance/   |     | Cancelled     |
       +-------+-------+     |  Contrast)    |     +---------------+
               |             +-------+-------+
               |                     |
               +----------+----------+
                          |
                          v
                  +---------------+
                  |Status:        |
                  |Completed      |
                  +---------------+
```

## 3. Database Schema Updates
- Added `locked_by: Mapped[str | None] = mapped_column(String(128), nullable=True)` to `tryon_jobs`.
- Alembic Migration `0031_tryon_jobs_locked_by`:
  - Upgrades `tryon_jobs` with `locked_by VARCHAR(128)` column and index `ix_tryon_jobs_queue_locked`.
  - Downgrades cleanly by dropping index and column.

## 4. Key Contracts & Interfaces
- **CreateTryOnCommand / CreateTryOnResult:** Command/result payload for job enqueueing.
- **TryOnWorker:** Heartbeat-enabled worker executing `claim_job()`, `process_one()`, and `run_loop()`.
- **TryOnJobRepository:**
  - `create(...)`: Idempotent insert or retrieval of existing job.
  - `claim_next_job(worker_id, lease_seconds)`: Atomic claim with worker lease.
  - `renew_lease(job_id, worker_id, lease_seconds)`: Heartbeat lease renewal.
  - `release_lease(job_id, worker_id)`: Cleanup of active lease.
  - `request_cancel(job_id, user_id)`: Immediate or cooperative cancellation.
  - `get_owned(job_id, user_id)`: Owner-scoped retrieval.
