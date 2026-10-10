# Phase 5 Task Log: Real Try-On Path and Adapter

**Date:** 2026-10-10  
**Branches:** `feat/phase5a-tryon-foundation`, `feat/phase5b-tryon-real-adapter`, `feat/phase5c-eval-decision`  
**Tags:** `v0.5-real-tryon`  
**Goal:** Deliver a license-cleared virtual try-on pipeline that executes end-to-end via the API on real models, with a measured quality, latency, and cost scorecard, clear Gate G5 (commercial clearance), and establish capability gating for complex garment structures.

---

## 1. Architecture Decisions & Implementation

### PR 5A: Try-On Foundation, Licensing Guard & Adapter Protocol
- **Model License Register:** Authored [`docs/architecture/model-licenses.md`](../architecture/model-licenses.md) documenting and cataloging try-on models. Formally blocks all non-commercial research models (StableVITON, OOTDiffusion, IDM-VTON, CatVTON, VITON-HD, HR-VITON) in accordance with Rule I08.
- **Runtime License Guard:** Implemented `assert_production_license` in [`backend/fashx/ml/licenses.py`](../../backend/fashx/ml/licenses.py) enforcing `ALLOWED_LICENSE_IDS = {"commercial-api", "apache-2.0", "mit"}` when `ENV=prod`. Startup and job submission immediately fail if unapproved models are selected.
- **Two-Phase Adapter Port:** Designed canonical `TryOnAdapter` protocol in [`backend/fashx/application/ports/tryon.py`](../../backend/fashx/application/ports/tryon.py) decoupling submission (`submit_job`) from status collection (`collect_job`), supporting async polling and webhook architectures.
- **MockAdapter Parity:** Updated `MockAdapter` to implement the two-phase protocol with license checking, maintaining seamless local development and CI testing.
- **Database Migration `0017_tryon_provider_tracking`:**
  - Added `tryon_usage` table for anonymized cost accounting (storing provider, cost_usd, latency_ms, status without user PII linkage).
  - Added `provider`, `provider_job_id`, and `attempts` columns to `tryon_jobs` table in [`database/models/tryon.py`](../../database/models/tryon.py).

### PR 5B: Real Adapter, Resilient Worker & Circuit Breakers
- **Image Preparation Pipeline:** Implemented `prepare_for_provider` in [`backend/fashx/ml/prep.py`](../../backend/fashx/ml/prep.py) with Lanczos downsampling (max dimension 1536px), EXIF stripping, and RGB JPEG encoding.
- **Hosted FASHN API Adapter:** Implemented `FashnApiAdapter` in [`backend/fashx/infrastructure/tryon/fashn_api.py`](../../backend/fashx/infrastructure/tryon/fashn_api.py):
  - Supports both `tryon-v1.6` and `Try-On Max` models.
  - Implements two-phase execution with poll backoff.
  - SSRF defense preventing malicious provider output URLs by validating against allowed hostnames.
  - Granular error mapping: `TryOnError`, `TryOnQuotaExceeded`, `TryOnTimeoutError`, `TryOnContentModerationError`.
- **Circuit Breaker & Safety Guards:** Implemented `Breaker` in [`backend/fashx/ml/breaker.py`](../../backend/fashx/ml/breaker.py):
  - Redis-backed circuit breaker with local in-memory fallback.
  - Dialect-neutral daily budget cap check (`check_daily_budget_exceeded`) using Python UTC date math compatible with both SQLite and PostgreSQL.
  - Per-user daily submission rate limit check (`check_user_daily_cap_exceeded`).
- **Resumable Worker Orchestration:** Enhanced `process_tryon_job` in [`backend/fashx/tryon/application/process_job.py`](../../backend/fashx/tryon/application/process_job.py):
  - Records `provider_job_id` before polling starts, enabling job recovery on worker restart.
  - In-flight consent re-validation: verifies user consent has not been revoked during generation before storing result images.
  - C2PA synthetic media provenance watermarking on all outputs.
  - Outputs stored directly to private user-scoped object storage keys (`u/<user_id>/tryon/<job_id>.jpg`).
  - Anonymized cost and latency recorded in `tryon_usage`.

### PR 5C: Evaluation, Capability Gating & Gate G5 Clearance
- **Evaluation & Scoring Harness:** Authored evaluation tools under `scripts/tryon_eval/`:
  - `run_eval.py`: Benchmark suite running across diverse body types, skin tones, and garment classes.
  - `make_rating_sheet.py`: Blinding rating sheet generator for human assessment.
  - `score.py`: Multi-metric scoring (acceptability, boundary alignment, skin tone preservation, artifact rates).
- **Capability Gating:**
  - Added `tryon_supported: Mapped[bool]` to [`database/models/catalog.py`](../../database/models/catalog.py).
  - Added `TRYON_SUPPORTED_CATEGORIES` setting to [`backend/fashx/core/settings.py`](../../backend/fashx/core/settings.py).
  - Enforced gating in [`backend/fashx/tryon/application/submit_job.py`](../../backend/fashx/tryon/application/submit_job.py): rejects unsupported garments (e.g., complex unanchored draped ethnic wear like Sarees and Lehengas) with HTTP 422 `unsupported_garment`.
- **Data Flows & Privacy Architecture:** Documented end-to-end data flows and sub-processor terms in [`docs/architecture/data-flows.md`](../architecture/data-flows.md):
  - 72-hour automated vendor deletion guarantee.
  - Signed DPA sub-processor terms complying with DPDP requirements.
  - Strict adult-only pilot boundary.
- **Evaluation Scorecard:** Published evaluation findings in [`docs/logs/phase5-eval-2026-10-10.md`](phase5-eval-2026-10-10.md):
  - 97.5% completion rate (vs ≥ 95% threshold).
  - 76.2% acceptability on supported categories (vs ≥ 70% threshold).
  - 96.2% identity and skin tone preservation (vs ≥ 95% threshold).
  - 11.4 s p95 vendor latency (vs ≤ 30 s threshold).
  - $0.0984 cost per accepted result (vs ≤ $0.1500 threshold).
- **ADR-0004 Finalization:** Formally accepted [`docs/adr/0004-tryon-provider.md`](../adr/0004-tryon-provider.md) selecting Candidate A (FASHN Hosted API) with capability gating.

---

## 2. Verification & Quality Metrics

- **Pytest:** 1,117 passed, 2 skipped (requiring live external Postgres), 244 deselected (frozen) = 1,363 total tests.
- **Ruff:** 0 errors in active codebase.
- **Mypy:** 0 type issues across 802 files.
- **Alembic:** 17 migrations, single head, clean schema alignment.
- **Git Hygiene:** No eval images, API keys, or raw vendor URLs committed to repository.

---

## 3. Release Gates Impact

| Gate | Status | Notes |
|---|---|---|
| **G1 Functional** | 🟡 | E2E on mocks and real FASHN adapter contracts passing. |
| **G2 ML Quality** | 🟡 | 76.2% acceptability on supported categories (tops/bottoms/one-pieces). Complex draped garments gated. |
| **G3 Performance** | 🟡 | Measured p95 vendor latency 11.4s, total queue+run p95 13.8s at concurrency 3. |
| **G4 Privacy** | 🟡 | Verified 72h vendor auto-delete DPA terms, in-flight consent re-check, and Outbox erasure pattern. |
| **G5 Commercial Clearance** | ✅ | **CLEARED:** Commercial model license registered, vendor DPA executed, non-commercial models banned (Rule I08). |
| **G6 User Acceptance** | ⬜ | Pending real user pilot. |
