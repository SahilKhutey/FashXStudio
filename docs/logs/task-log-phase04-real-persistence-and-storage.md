# Phase 4 Task Log: Real Persistence and Storage

**Date:** 2026-10-09  
**Branches:** `feat/phase4a-audit-infrastructure`, `feat/phase4b-sql-repositories`, `feat/phase4c-storage-erasure`  
**Tags:** `v0.4-real-persistence`  
**Goal:** Deliver complete data persistence across server restarts: all MVP domains read and write PostgreSQL via dual SQLAlchemy/In-Memory adapters with 100% contract parity, photos and try-on results live in private S3/R2 storage behind expiring signed capability URLs (Rule I06), and consent revocation triggers verifiable cascading erasure (Gate G4).

---

## 1. Architecture Decisions & Implementation

### PR 4A: Audit, Test Infrastructure & Wiring Switch
- **ADR 0002 Persistence Pattern:** Authored [`docs/adr/0002-sql-persistence.md`](../adr/0002-sql-persistence.md) establishing ports & adapters with domain purity (Rule I03). Domain code interacts purely through repository ports; SQLAlchemy ORM models never escape the repository boundaries.
- **Contract Test Suite Infrastructure:** Authored reusable contract tests under `tests/contracts/` designed to execute against both in-memory and PostgreSQL adapters.
- **Fail-Fast Production Validation:** Added `REPO_BACKEND` setting in [`backend/fashx/core/settings.py`](../../backend/fashx/core/settings.py) enforcing `REPO_BACKEND=sql` when `ENV=prod`. Startup immediately halts if in-memory repositories are configured in production.
- **Database Engine & Session Management:** Configured connection pooling, schema isolation, and transaction rollback hooks in `backend/fashx/core/database.py`.

### PR 4B: SQL Repositories per Domain & Restart Persistence
- **SQLAlchemy Repository Adapters:** Implemented SQL adapters for all MVP domains:
  - Identity / Profile: Users, measurements, user photos, consents, preferences.
  - Catalog: Garments, categories, brand metadata, and pgvector embeddings.
  - Try-on: Asynchronous try-on jobs, status transitions, and artifact references.
  - Fit Feedback: User fit outcomes, ratings, and return correlation entries.
  - Closet: Saved items, collections, price snapshots, and availability.
  - Recommendations & Trends: Precomputed candidate sets, trend scores, and user interactions.
- **Transactional Outbox Pattern:**
  - Implemented Outbox pattern in `backend/fashx/integration/outbox.py`.
  - Added Alembic migration `0015_outbox_pattern.py`.
  - Ensures atomic domain events and cross-service messaging without distributed transaction overhead.
- **Contract Test Parity:** Verified all 8 contract test suites across both In-Memory and SQL adapters with zero discrepancies.
- **Cold-Start Verification:** Verified end-to-end restart persistence using restart script and simulated persistence cycles.

### PR 4C: Object Storage and Erasure Pipeline (Gate G4)
- **ADR 0003 Object Storage Architecture:** Authored [`docs/adr/0003-object-storage.md`](../adr/0003-object-storage.md) establishing Cloudflare R2 / AWS S3 compatibility, private bucket posture, key hierarchy (`u/<user_id>/...`), and capability URLs.
- **Canonical Storage Port & Adapters:**
  - Port: Defined `ObjectStorage` protocol in [`backend/fashx/application/ports/storage.py`](../../backend/fashx/application/ports/storage.py).
  - S3 / R2 Adapter: Implemented `S3Storage` in [`backend/fashx/infrastructure/storage/s3.py`](../../backend/fashx/infrastructure/storage/s3.py) with presigned URLs, prefix deletion, and automatic pagination (>1000 items).
  - Local Adapter: Implemented `LocalStorage` in [`backend/fashx/infrastructure/storage/local.py`](../../backend/fashx/infrastructure/storage/local.py) for dev/test environments with HMAC capability URLs (`/dev-files/...`) and strict fail-fast refusal when `ENV=prod`.
- **Database Metadata Only (Rule I06):**
  - Database stores object keys only, never URLs or raw image binaries.
  - Added `MediaObject` ORM entity and Alembic migration `0016_media_objects.py`.
- **Dynamic Capability Signing:**
  - `POST /api/v1/profile/{user_id}/photos` sanitizes photos, uploads to storage, and tracks keys.
  - `GET /api/v1/profile/{user_id}/photos/{media_id}/url` produces expiring signed URLs (default 300s TTL).
  - `GET /api/v1/tryon/jobs/{job_id}` dynamically generates signed capability URLs for output artifacts on every request.
- **Cascading Erasure & Right to Erasure:**
  - Implemented `erase_biometrics` and `erase_account` in [`backend/fashx/application/erasure.py`](../../backend/fashx/application/erasure.py).
  - Outbox integration emitting `StoragePurgeRequested` events for reliable background storage deletion.
  - Added `DELETE /api/v1/me` (returning HTTP 202 Accepted).
  - Table classification guard test (`test_every_model_table_is_classified`) enforces classification for every table containing `user_id`.
- **Operational Tooling:**
  - Maintenance orphan sweeper script: [`scripts/maintenance/sweep_orphans.py`](../../scripts/maintenance/sweep_orphans.py).
  - PostgreSQL backup script: [`scripts/maintenance/backup_db.ps1`](../../scripts/maintenance/backup_db.ps1).
  - Real bucket verification guide: [`docs/logs/phase4-real-bucket-check.md`](phase4-real-bucket-check.md).

---

## 2. Verification & Quality Metrics

- **Pytest:** 1,089 passed, 0 failed, 2 skipped (requiring live external Postgres), 244 deselected (frozen) = 1,334 total tests.
- **Contract Test Suites:** 8 suites passing 100% on both LocalStorage / In-Memory and Moto S3 / SQL.
- **Alembic Revisions:** 16 migrations (`0016_media_objects (head)`).
- **Ruff & Mypy:** 0 lint errors, 0 type issues across active codebase.
- **Threat Model Mitigation:** T9 (Public bucket exposure) and T10 (Residual biometric data) verified and marked mitigated in `docs/architecture/threat-model.md`.
