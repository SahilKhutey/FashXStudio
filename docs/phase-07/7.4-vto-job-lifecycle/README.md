# Phase 07.4 — Complete VTO Job Lifecycle

## 1. Objective
Build one reliable, asynchronous, secure virtual try-on lifecycle that accepts a shopper's virtual try-on request, validates authorization and inputs, submits inference to the selected provider, retrieves and validates the generated image, stores it privately, and makes the result accessible only to the requesting shopper.

The database is the durable source of truth for every job. A queue message is only a delivery signal; it must never be the only record that a job exists or what state it is in.

---

## 2. Scope & Integration Boundaries
This phase connects and unifies:
- **Phase 05**: Authorized merchant catalog, product images, image permissions (`IMAGE_AI_PROCESS`, `VTO_PROCESS`), and merchant takedowns.
- **Phase 04**: Shopper authentication, portrait photo ownership, consent (`THIRD_PARTY_VTO_PROCESSING`), and private image storage.
- **Phase 07.2**: Provider configuration, FASHN adapter, error normalization, rate limits, and cost accounting.
- **Phase 07.3**: Mandatory shopper-image and garment-image validation gate.

---

## 3. Core Lifecycle Rules
1. **Asynchronous Non-Blocking API**: The API accepts the request, verifies authorization and inputs, commits the job and outbox message transactionally, and returns HTTP 202 Accepted. It never holds an open HTTP connection while waiting for inference.
2. **Durable Job Persistence**: The job record is committed before the worker can process it.
3. **Idempotency & Reusable Results**: Client requests supply an `Idempotency-Key`. Canonical request hashes detect key reuse with different payloads (returning HTTP 409 Conflict). Safe result reuse checks ownership, consent, permissions, versions, and retention.
4. **Lease-Based Worker Ownership**: Workers atomically claim jobs with leases. Stale workers cannot overwrite a newer worker's state (`transition_if_owned`).
5. **No Blind Resubmissions**: Provider submission attempts are recorded before sending. A timeout during submit moves the attempt to `UNKNOWN` and job to `SUBMISSION_UNKNOWN` to avoid duplicate billing.
6. **Untrusted Output Boundary**: Provider outputs are treated as untrusted external data. Downloads are guarded against SSRF, fully decoded with Pillow, validated against size/pixel bounds, normalized to clean JPEG, and hashed before private S3 storage.
7. **Atomic Completion**: A job moves to `COMPLETED` only after the validated output is stored in private S3, verified via storage `head()`, and artifact metadata is committed.
8. **Owner-Only Result Access**: Results are accessible only to the authenticated owner. Probing another user's job returns a generic 404 without disclosing existence.

---

## 4. Key Reused Components
- `database/models/tryon.py`: `TryOnJob`, `TryOnArtifact`, `TryOnUsage`, `TryOnInputValidation`, `TryOnInputAuthorizationSnapshot`
- `database/models/operations.py`: `OutboxMessageRecord`
- `backend/fashx/integration/outbox.py`: `SqlOutboxRepository`
- `backend/fashx/tryon/validation/`: Image inspection, category policy, visual assessment, shopper validator, garment validator, combined validator
- `backend/fashx/infrastructure/tryon/fashn_api.py`: `FashnApiAdapter`
- `backend/fashx/infrastructure/storage/s3.py`: `S3Storage`
- `backend/fashx/workers/app.py`: Celery worker task configuration

---

## 5. Verification Status
- **Implementation Status**: 🟢 IN_PROGRESS (Repository audit completed; contracts, models, migrations, validators, and worker hardening underway).
- **Unit Test Status**: 🟢 PENDING_EXECUTION
- **Staging Acceptance**: 🟡 PENDING_STAGING_DEPLOYMENT
