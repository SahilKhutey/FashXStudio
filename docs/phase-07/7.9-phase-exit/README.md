# Phase 07.9 — VTO Deliverables and Production Exit Gate

## 1. Objective

Phase 07.9 is the integration, verification, and release-acceptance audit for the complete FashXStudio Virtual Try-On (VTO) subsystem.

The objective is to prove that an authorized shopper can complete the entire workflow using an authorized product image and a real or configured VTO provider, retrieving validated results securely while enforcing strict separation between visual try-on simulation and physical fit prediction.

## 2. Subsystem Scope

Phase 07 integrates capabilities across 8 dedicated development sub-phases:
1. **Live Provider Connection (7.2)**: Provider-neutral adapter interface (`TryOnProviderPort`), FASHN provider adapter, and mock provider adapter.
2. **Input Validation (7.3)**: Shopper consent validation, image integrity, face detection, resolution thresholds, garment isolation, and merchant permissions.
3. **Complete Job Lifecycle (7.4)**: Durable PostgreSQL job records, outbox pattern, queue dispatch, immutable input snapshots, and owner-only result retrieval.
4. **Reliability and Failure Handling (7.5)**: Strict job state machine, transient vs permanent error classification, exponential backoff, worker lease recovery, and dead-letter queues.
5. **Caching and Cost Controls (7.6)**: Canonical cache keys, TTL expiration, invalidation on image deletion/takedown, usage accounting, per-user/merchant quotas, and emergency kill switches.
6. **VTO Quality Evaluation (7.7)**: Permissioned evaluation datasets, automated quality metrics (LPIPS, SSIM, garment preservation), human rating rubrics, and category-level gates.
7. **Visual Try-On vs Fit Prediction Separation (7.8)**: Platform-wide disclosure (`VISUAL_TRYON_NOT_FIT_VERIFICATION`), prohibition of fit guarantee copy, merchant size charts, and shopper reporting.
8. **Phase Exit Gate & Integration (7.9)**: Master integration test suite, repository audit, operational runbooks, security isolation, and staging acceptance.

## 3. Non-Negotiable Operational Invariants

- **PostgreSQL is the durable source of truth**: Queue brokers (Redis/Celery) are delivery mechanisms only; state transitions, snapshots, and idempotency keys persist durably.
- **Provider secrets never leak**: API keys and vendor credentials never enter client payloads, error traces, or metric tags.
- **Paid inference is protected against duplicates**: Canonical request fingerprints and idempotency keys prevent duplicate charges.
- **Visual Try-On != Fit Prediction**: All VTO outputs explicitly state `fit_verified: false` and include mandatory disclosure. VTO images are strictly prohibited as evidence for physical fit recommendations.
- **Fail-Closed on Unverified Assets**: If consent is revoked, an image is taken down, or a category is unsupported (e.g. sarees, lehengas), inference and fit recommendations fail closed.
- **No Simulated Real-World Evidence**: Under repository rule AGENTS.md, evidence cards and production approvals require actual human founder runs against external APIs.

## 4. Current Phase Status

- **Architecture & Code**: Complete across all 8 sub-phases (`backend/fashx/tryon/`, `backend/fashx/fit/`, `backend/fashx/presentation/`, `backend/fashx/catalog/size_charts/`).
- **Automated Verification**: **260 automated unit and integration tests passing** (`python tests/unit/tryon/run_phase07_exit_gate.py`).
- **Environment Status**: `ALL PHASE 07 GATES PASSED [LOCAL / SANDBOX]`.
- **Production Exit Acceptance**: `CONDITIONAL / PENDING OPERATOR STAGING RUN` (Awaiting live FASHN external API key and shared staging PostgreSQL execution by human operator).

## 5. Documentation Package Structure

| Document | Purpose |
| :--- | :--- |
| `repository-audit.md` | Verification of existing codebase, modules, models, and migrations |
| `deliverables-matrix.md` | Comprehensive status tracking table for deliverables 7.9.1 - 7.9.10 |
| `architecture-verification.md` | End-to-end service interaction, state machine, and data flow |
| `integration-test-plan.md` | End-to-end integration scenarios and automated test coverage |
| `live-provider-test-plan.md` | Bounded live provider execution and verification procedures |
| `security-verification.md` | Secrets isolation, signed URL boundaries, and cross-user security |
| `reliability-test-plan.md` | State transition integrity, failure injection, recovery, and DLQ |
| `cache-and-cost-verification.md` | Cache keys, invalidation triggers, ledgers, and spend limits |
| `evaluation-dataset-acceptance.md` | Dataset governance, demographic balance, and consent records |
| `quality-report.md` | Measured provider output quality, benchmark metrics, and category gates |
| `staging-test-report.md` | Verification test execution log and local gate results |
| `production-readiness-review.md` | Gates A-F acceptance criteria and operational blockers |
| `operational-runbook.md` | Metric definitions, alert thresholds, and incident remediation steps |
| `known-limitations.md` | Supported/unsupported categories, single-garment limits, and risks |
| `phase-07-exit-approval.md` | Formal conditional exit decision and verification record |
