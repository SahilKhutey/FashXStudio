# RC05 — 01 VTO Architecture

## Objective
Define the comprehensive end-to-end Virtual Try-On target architecture spanning client interactions, authenticated gateway routes, background task queues, GPU worker claiming, third-party provider execution, post-processing validation, and artifact delivery.

## Existing State
- Fragmented execution pathways between Celery task queue dispatching and synchronous or worker polling loops.
- Incomplete observability when Celery broker was unavailable during job submission.

## Changes
- Unified pipeline flow ensuring persistent job state in PostgreSQL is the single source of truth.
- Decoupled job queue dispatching from request completion: persistent jobs are created before dispatching, and dispatching reports observable `DispatchResult`.

## Architecture Diagram
```mermaid
sequenceDiagram
    autonumber
    actor User as Mobile User (Expo)
    participant API as FastAPI Backend (/api/v1/tryon)
    participant DB as PostgreSQL (Jobs & Artifacts)
    participant Q as Redis / Celery Queue
    participant W as TryOnWorker (Worker Loop)
    participant PV as Provider (FASHN / Mock)
    participant ST as Object Storage (S3 / Local)

    User->>API: POST /tryon/jobs (Idempotency-Key, garment_id, [photo_id])
    API->>DB: Check consent (body_photo), photo status, garment eligibility
    API->>DB: Compute cache key & persist TryOnJob (status='queued')
    API->>Q: Dispatch job_id (non-blocking)
    API-->>User: 202 Accepted (job_id, status='queued', artifact_key)

    W->>DB: Atomically claim next queued job (lease=180s)
    W->>DB: Re-verify user active consent
    W->>PV: Submit normalized person & garment images
    PV-->>W: Return provider_job_id
    W->>DB: Persist provider_job_id & status='processing'

    loop Status Polling
        User->>API: GET /tryon/jobs/{job_id}
        API-->>User: 200 OK (status, progress, signed URLs)
        W->>PV: Poll provider_job_id status
    end

    PV-->>W: Rendered image bytes
    W->>W: Post-inference quality check (luminance, contrast, dimensions)
    W->>W: Apply C2PA metadata & Synthetic Watermark
    W->>ST: Store artifact at u/{user_id}/tryon/{job_id}.png
    W->>DB: Record TryOnArtifact & status='completed'

    User->>API: GET /tryon/jobs/{job_id}
    API-->>User: 200 OK (status='completed', signed result_url, artifact_id)
    User->>API: POST /wardrobe/items (Save to closet)
    User->>API: POST /feedback/tryon (Accuracy rating & issue tags)
```

## Contracts
- Data flow enforces strict owner isolation at every hop.
- All artifact URLs generated as time-limited, expiring signed URLs.

## Implementation
- Documented in `backend/fashx/tryon/` and `backend/fashx/workers/`.
- Worker claims jobs using `SELECT FOR UPDATE SKIP LOCKED` patterns.

## Execution
- API server handles authenticated HTTP ingress.
- Workers can operate as Celery workers or independent database-polling instances.

## Tests
- Tested via `tests/integration/test_tryon_orchestration.py` and `scripts/rc05_vto_smoke.py`.

## Risks
- Double execution during worker restart.
- Mitigation: Atomic job claiming and persistence of `provider_job_id` before polling prevents redundant inference.

## Evidence
- Smoke test verified 8/8 end-to-end phases cleanly.

## Exit Criteria
- System architecture clearly defined and mapped to concrete codebase modules.
