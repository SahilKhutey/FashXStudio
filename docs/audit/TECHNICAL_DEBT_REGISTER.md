# FashXStudio Technical Debt Register

**Status:** Active
**Effective Date:** 2026-11-11
**Category:** Engineering Governance and Audit
**Classification:** Consolidated Baseline (Phase 02 Audit)

---

## 1. Overview and Priority Definitions

This register tracks all technical, operational, integration, and governance debt identified across FashXStudio during the Phase 02 audit. Debt items are prioritized as follows:

- **P0 (Critical):** Blocks a trustworthy MVP, violates governance, or poses material security, privacy, or legal risks. Must be resolved or explicitly risk-accepted by the human founder prior to pilot launch.
- **P1 (High):** Blocks pilot-quality release or essential operational validation. Must be addressed during pilot preparation.
- **P2 (Medium):** Maintainability, quality, or performance debt that can be planned into regular engineering sprints.
- **P3 (Low):** Minor technical cleanup or low-risk enhancements.

---

## 2. Technical Debt Records

### TD-001: Mock Virtual Try-On is Active Runtime Default
- **Title:** Mock VTO Adapter Active by Default
- **Description:** `TRYON_PROVIDER` in `backend/fashx/core/settings.py` defaults to `mock`. Image generation uses deterministic Pillow overlay rather than generative AI try-on models.
- **Evidence:** `TRYON_PROVIDER: Literal["mock", "fashn_api", "fashn_selfhost"] = "mock"` in `backend/fashx/core/settings.py`.
- **Impact:** Users and stakeholders may mistake synthetic mock output for functional AI try-on.
- **Priority:** P0
- **Affected Subsystem:** VTO (`backend/fashx/tryon/`)
- **Owner:** VTO Lead
- **Proposed Remediation:** Retain mock visibly labeled in UI during development; validate real provider adapter in sandbox; implement fail-fast check rejecting mock in production environment.
- **Dependencies:** Provider commercial agreement, API key provisioning.
- **Acceptance Criteria:** Production environment startup fails if `TRYON_PROVIDER=mock`; mobile UI displays clear preview indicator when mock adapter is active.
- **Status:** OPEN
- **Created Date:** 2026-11-11 | **Last Reviewed:** 2026-11-11

---

### TD-002: Real Provider Inference Unverified
- **Title:** Live FASHN Provider Inference Unexecuted
- **Description:** The HTTP adapter for FASHN exists (`backend/fashx/infrastructure/tryon/fashn_api.py`), but no live commercial inference has been executed or verified with external evidence.
- **Evidence:** `INTEGRATION_STATUS.csv` records `FASHN Hosted API` status as `LOCAL` with zero production or sandbox execution evidence.
- **Impact:** Core value proposition and latency/quality SLAs of the product remain technically unproven.
- **Priority:** P0
- **Affected Subsystem:** VTO / External Integrations
- **Owner:** VTO Lead / Tech Lead
- **Proposed Remediation:** Execute an authorized, single-image test inference in the provider's sandbox using test garments; record latency, response schema, and image fidelity.
- **Dependencies:** Commercial API credentials, test budget authorization.
- **Acceptance Criteria:** Provider returns HTTP 200 with completed job status and valid image artifact within SLA (<30s).
- **Status:** OPEN
- **Created Date:** 2026-11-11 | **Last Reviewed:** 2026-11-11

---

### TD-003: In-Memory Repository Default Requires Runtime Confirmation
- **Title:** In-Memory Persistence Default in Settings
- **Description:** `REPO_BACKEND` defaults to `memory` in `backend/fashx/core/settings.py`, risking silent data loss across container or server restarts if misconfigured.
- **Evidence:** `REPO_BACKEND: Literal["memory", "postgres"] = "memory"` in `settings.py`.
- **Impact:** Application data (profiles, wardrobes, jobs) will vanish on worker restarts in non-production deployments.
- **Priority:** P0
- **Affected Subsystem:** Persistence (`backend/fashx/infrastructure/repositories/`)
- **Owner:** Backend Lead
- **Proposed Remediation:** Verify that startup bootstrap switches to PostgreSQL whenever `DATABASE_URL` is set; enforce `REPO_BACKEND=postgres` in staging and production configurations.
- **Dependencies:** PostgreSQL database connectivity.
- **Acceptance Criteria:** Application refuses startup in `prod` or `staging` if `REPO_BACKEND != postgres`.
- **Status:** OPEN
- **Created Date:** 2026-11-11 | **Last Reviewed:** 2026-11-11

---

### TD-004: Production Object Storage Unverified
- **Title:** Live S3/R2 Cloud Bucket Unverified
- **Description:** Storage adapter (`backend/fashx/infrastructure/storage/s3.py`) supports S3/R2, but runtime tests currently use local disk storage (`STORAGE_BACKEND=local`).
- **Evidence:** `STORAGE_BACKEND=local` active in local environment; zero S3 bucket credentials or integration test runs against live buckets.
- **Impact:** Presigned upload URLs, private access restrictions, and photo lifecycle deletion remain unvalidated against cloud storage APIs.
- **Priority:** P0
- **Affected Subsystem:** Storage (`backend/fashx/infrastructure/storage/`)
- **Owner:** DevOps / Backend Lead
- **Proposed Remediation:** Provision an isolated staging S3/R2 bucket with zero-public-access policy and CORS configuration; run integration tests for upload, signed download, and deletion.
- **Dependencies:** Cloud provider credentials (AWS/Cloudflare).
- **Acceptance Criteria:** Automated test uploads fixture image, retrieves valid signed URL, validates expire time, and deletes object.
- **Status:** OPEN
- **Created Date:** 2026-11-11 | **Last Reviewed:** 2026-11-11

---

### TD-005: External Authentication Provider Unverified
- **Title:** Live JWKS Identity Provider Unverified
- **Description:** Local JWT generation and verification pass unit tests, but integration with external identity providers (Supabase Auth / Auth0) via JWKS is unverified.
- **Evidence:** `AUTH_MODE=local` active; `AUTH_JWKS_URL` unset in local environment.
- **Impact:** Social login, token refresh flows, and multi-factor authentication cannot be tested on mobile.
- **Priority:** P0
- **Affected Subsystem:** Authentication (`backend/fashx/security/`)
- **Owner:** Security Lead
- **Proposed Remediation:** Stand up a staging Supabase/Auth0 tenant; configure `AUTH_JWKS_URL`; execute contract test validating token verification against real JWKS keyset.
- **Dependencies:** Identity provider tenant setup.
- **Acceptance Criteria:** Backend accepts valid JWT issued by external provider and rejects forged or expired tokens.
- **Status:** OPEN
- **Created Date:** 2026-11-11 | **Last Reviewed:** 2026-11-11

---

### TD-006: No Live Merchant Catalog Feed Verified
- **Title:** Live Brand Partner Feed Ingestion Unverified
- **Description:** Catalog ingestion operates against static CSV fixtures (`scripts/catalog/seed_local.py`); live merchant sync (Shopify app, SFTP, partner CSV feed) has not been connected.
- **Evidence:** `INTEGRATION_STATUS.csv` lists `Partner Feed Ingestion` status as `LOCAL` with mock CSV fixtures only.
- **Impact:** Discovery catalog contains synthetic and sample products rather than live commercial inventory.
- **Priority:** P0
- **Affected Subsystem:** Catalog (`backend/fashx/catalog/acquisition/`)
- **Owner:** Catalog Lead / Commercial Lead
- **Proposed Remediation:** Partner with an approved design/retail partner to ingest a real 50-item product catalog via secure feed; validate provenance, copyright clearance, and SKU normalization.
- **Dependencies:** Partner legal consent and catalog data agreement.
- **Acceptance Criteria:** Ingestion pipeline successfully parses, enriches, deduplicates, and persists 50 real partner garments.
- **Status:** OPEN
- **Created Date:** 2026-11-11 | **Last Reviewed:** 2026-11-11

---

### TD-007: No Real User Pilot
- **Title:** Zero Real-User Pilot Validation
- **Description:** Historical pilot metrics in `docs/` were generated during commercial rehearsals and simulations; zero real shoppers have completed the end-to-end try-on journey.
- **Evidence:** `docs/provenance.md` explicitly quarentines pilot and commercial metrics as unverified simulations; `docs/STATUS.md` records release gates as NOT MEASURED.
- **Impact:** Commercial and conversion hypotheses remain unvalidated in real market conditions.
- **Priority:** P0
- **Affected Subsystem:** Pilot / Product Governance
- **Owner:** Human Founder / Product Lead
- **Proposed Remediation:** Execute a controlled, 10-person real-world pilot under the approved Pilot Protocol (Phase 1.1–1.4); capture actual user fit-satisfaction, latency, and feedback.
- **Dependencies:** P0 technical debt resolution (VTO, Auth, Storage, Privacy).
- **Acceptance Criteria:** 10 authentic users onboarded, consented, and verified with human evidence cards in `docs/evidence/`.
- **Status:** OPEN
- **Created Date:** 2026-11-11 | **Last Reviewed:** 2026-11-11

---

### TD-008: Evidence Evaluator Governance Gap
- **Title:** Release Gate Evaluator Weak Authentication
- **Description:** `scripts/rc13/evaluate_release_gates.py` historically accepted synthetic and unverified evidence records without strict cryptographic checksums or quarantine checks.
- **Evidence:** Remediation implemented in Phase 2.5 adding `--authenticate-evidence` and `validate_evidence_file` (PR #34, commit `1e78ac6`).
- **Impact:** Release gate evaluations could potentially pass based on placeholder or unverified evidence.
- **Priority:** P0
- **Affected Subsystem:** Governance / Release Infrastructure
- **Owner:** Release Lead
- **Proposed Remediation:** Complete review and merge of PR #34; ensure CI enforces evidence authentication on every release gate run.
- **Dependencies:** Human founder review of PR #34.
- **Acceptance Criteria:** PR #34 merged; `python scripts/rc13/evaluate_release_gates.py --authenticate-evidence` passes cleanly in CI.
- **Status:** IN_REVIEW
- **Created Date:** 2026-11-11 | **Last Reviewed:** 2026-11-11

---

### TD-009: Roadmap Rehearsal Metrics Reconciliation
- **Title:** Historical Roadmap Claims Inconsistent with Audit
- **Description:** Historical `docs/ROADMAP.md` presented simulated financial and pilot figures as completed milestones.
- **Evidence:** Reconciled in Phase 2.5 with dual-track architecture (Engineering Implementation vs Real-World Evidence) and explicit pre-pilot lifecycle stage.
- **Impact:** Potential stakeholder confusion regarding actual platform commercial traction.
- **Priority:** P0
- **Affected Subsystem:** Governance / Product Documentation
- **Owner:** Product Lead
- **Proposed Remediation:** Reconciled and committed in PR #34; maintain clear separation between code completion and real-world pilot verification.
- **Dependencies:** PR #34 merge.
- **Acceptance Criteria:** `docs/ROADMAP.md` accurately identifies lifecycle as "Pre-pilot engineering validation".
- **Status:** IN_REVIEW
- **Created Date:** 2026-11-11 | **Last Reviewed:** 2026-11-11

---

### TD-010: Status Report Staleness
- **Title:** Stale docs/STATUS.md Report
- **Description:** The root status report was dated October 24, 2026, and did not reflect current test baselines or Phase 02 audit outcomes.
- **Evidence:** Updated to 2026-11-11 in PR #34, recording 1,066 unit tests, 165 mobile tests, and explicit HOLD status.
- **Impact:** Misrepresentation of active engineering state.
- **Priority:** P1
- **Affected Subsystem:** Governance / Documentation
- **Owner:** Tech Lead
- **Proposed Remediation:** Keep `docs/STATUS.md` synchronized with Phase 02 audit deliverables; enforce `docs_lint.py` checks.
- **Dependencies:** Phase 02 baseline approval.
- **Acceptance Criteria:** `docs/STATUS.md` reflects latest verified test results and zero unsupported ✅ marks.
- **Status:** IN_REVIEW
- **Created Date:** 2026-11-11 | **Last Reviewed:** 2026-11-11

---

### TD-011: Historical Test-Count Discrepancies
- **Title:** Inconsistent Test Counts in Documentation
- **Description:** Previous documentation cited disparate test counts (e.g., 360 test files, 152 mobile tests) that did not match actual execution.
- **Evidence:** Audited and verified in Phase 02.3 and 2.7: 2,060 collected items; 1,066 unit passed; 1,777 non-frozen passed; 22 mobile test suites (165 tests passed).
- **Impact:** Ambiguity in quality reporting.
- **Priority:** P1
- **Affected Subsystem:** QA / Test Engineering
- **Owner:** QA Lead
- **Proposed Remediation:** Standardize on exact output from `pytest` and `jest` execution logs in all audit documents.
- **Dependencies:** None.
- **Acceptance Criteria:** All test documentation references the verified baseline figures.
- **Status:** RESOLVED
- **Created Date:** 2026-11-11 | **Last Reviewed:** 2026-11-11

---

### TD-012: Fake Semantic Embeddings Default
- **Title:** Hash-Based Fake Embeddings Active by Default
- **Description:** Catalog embedding uses a deterministic fake embedder (`backend/fashx/catalog/embeddings/fake.py`) hashing text strings rather than a genuine vision-language model.
- **Evidence:** `FakeEmbedder` active when FashionCLIP model weights are not installed locally.
- **Impact:** Recommendation and discovery ranking operates on arbitrary vectors rather than real visual-semantic similarity.
- **Priority:** P1
- **Affected Subsystem:** Discovery / ML (`backend/fashx/catalog/embeddings/`)
- **Owner:** ML Lead
- **Proposed Remediation:** Evaluate pre-computed Marqo FashionCLIP or cloud embedding API for catalog products during pilot preparation.
- **Dependencies:** GPU inference infrastructure or hosted embedding endpoint.
- **Acceptance Criteria:** Discovery ranking benchmark demonstrates statistically significant relevance improvement over fake hash baseline.
- **Status:** OPEN
- **Created Date:** 2026-11-11 | **Last Reviewed:** 2026-11-11

---

### TD-013: Mock VLM Default for Catalog Enrichment
- **Title:** Rule-Based Mock VLM in Catalog Enrichment
- **Description:** Catalog garment feature extraction (neckline, sleeve length, occasion) defaults to a rule-based mock client rather than multimodal LLM analysis.
- **Evidence:** `VLM_PROVIDER=mock` default in `settings.py`.
- **Impact:** Catalog enrichment accuracy on unstandardized merchant descriptions is limited to simple regex matching.
- **Priority:** P1
- **Affected Subsystem:** Catalog Enrichment (`backend/fashx/catalog/enrichment/`)
- **Owner:** ML Lead
- **Proposed Remediation:** Benchmark Claude 3.5 Sonnet / GPT-4o Vision on a 50-item sample catalog; measure attribute extraction accuracy against manual labels.
- **Dependencies:** Multimodal API key provisioning.
- **Acceptance Criteria:** Real VLM achieves >90% precision on neckline, sleeve length, and pattern extraction on test dataset.
- **Status:** OPEN
- **Created Date:** 2026-11-11 | **Last Reviewed:** 2026-11-11

---

### TD-014: Merchant Platform Feature-Flagged Inactive
- **Title:** B2B Merchant APIs Gated by Inactive Flag
- **Description:** Merchant dashboard and tenant APIs (`backend/fashx/b2b/`) are disabled by default (`enable_b2b: bool = False`).
- **Evidence:** `ENABLE_B2B=false` in `.env.example` and `settings.py`.
- **Impact:** Merchant self-service, inventory upload, and analytics portals are non-functional in current build.
- **Priority:** P1
- **Affected Subsystem:** Merchant Platform (`backend/fashx/b2b/`)
- **Owner:** B2B Engineering Lead
- **Proposed Remediation:** Maintain disabled state for initial pilot MVP; validate tenant data isolation and permissions before activating flag for partner trial.
- **Dependencies:** Tenant isolation audit.
- **Acceptance Criteria:** Multi-tenant test suite confirms Merchant A cannot access Merchant B data when `enable_b2b=True`.
- **Status:** OPEN
- **Created Date:** 2026-11-11 | **Last Reviewed:** 2026-11-11

---

### TD-015: Physical Mobile Device Testing Pending
- **Title:** Mobile Client Not Validated on Physical Devices
- **Description:** All mobile test execution has occurred in Node.js / Jest headless simulation and Android Hermes bundle compilation; physical device sensors, camera permissions, and network transitions remain unvalidated.
- **Evidence:** Mobile tests pass in Jest (165 passed), but physical device test log does not exist.
- **Impact:** Real users may encounter camera crashes, aspect ratio distortion, memory pressure, or permission rejection bugs on low-end Android or iOS hardware.
- **Priority:** P1
- **Affected Subsystem:** Mobile Application (`mobile/`)
- **Owner:** Mobile Lead
- **Proposed Remediation:** Build staging APK/IPA via EAS; execute structured testing checklist on physical Android (Samsung/OnePlus) and iOS devices.
- **Dependencies:** EAS build pipeline and physical test devices.
- **Acceptance Criteria:** Physical device smoke test passes without unhandled exceptions across photo capture, onboarding, and wardrobe view.
- **Status:** OPEN
- **Created Date:** 2026-11-11 | **Last Reviewed:** 2026-11-11

---

### TD-016: Historical Backend Type Ignores
- **Title:** Type-Ignore Directives in Backend Modules
- **Description:** Historical audit notes indicated up to 67 `# type: ignore` directives across backend source files.
- **Evidence:** `mypy .` currently passes on 1,168 source files in CI, but legacy suppressions reduce type-safety guarantees.
- **Impact:** Refactoring risk and potential runtime `AttributeError` / `TypeError` bugs in edge-case code paths.
- **Priority:** P2
- **Affected Subsystem:** Backend Core
- **Owner:** Tech Lead
- **Proposed Remediation:** Grep and audit all `# type: ignore` comments in `backend/fashx/`; replace with explicit Pydantic schemas or type narrowing.
- **Dependencies:** None.
- **Acceptance Criteria:** Complete elimination or formal justification of all type-ignore suppressions per `AGENTS.md` Rule 4.
- **Status:** OPEN
- **Created Date:** 2026-11-11 | **Last Reviewed:** 2026-11-11

---

### TD-017: Lack of Staging Cloud Environment
- **Title:** Absence of Deployed Staging Environment
- **Description:** FashXStudio has zero deployed cloud instances (AWS, GCP, Railway, or Render); all execution is confined to local workstations and GitHub Actions ephemeral runners.
- **Evidence:** `README.md` and `docs/STATUS.md` state zero production cloud deployments exist.
- **Impact:** Cloud networking, SSL certificate termination, load balancer timeouts, and container startup latency remain unproven.
- **Priority:** P1
- **Affected Subsystem:** Infrastructure / DevOps
- **Owner:** DevOps Lead
- **Proposed Remediation:** Provision an isolated, low-cost staging environment (e.g., managed container service + PostgreSQL + Redis); deploy commit `0c23bb0` and verify `/healthz`.
- **Dependencies:** Cloud provider account and budget authorization.
- **Acceptance Criteria:** Staging environment accessible over HTTPS with healthy database and Redis status.
- **Status:** OPEN
- **Created Date:** 2026-11-11 | **Last Reviewed:** 2026-11-11

---

### TD-018: Incomplete Qualified Legal and Privacy Review
- **Title:** Biometric and Photograph Legal Review Incomplete
- **Description:** While technical privacy controls (DPDP consent logging, photo TTL, cascading deletion) are implemented in code, qualified external legal counsel has not signed off on the biometric consent flow or terms of service under Indian DPDP Act 2023 or GDPR.
- **Evidence:** `docs/audit/SUBSYSTEM_INVENTORY.csv` records privacy status as `PARTIAL` with external legal sign-off unverified.
- **Impact:** Material regulatory and legal liability when processing real user photographs.
- **Priority:** P0
- **Affected Subsystem:** Legal / Compliance / Profile
- **Owner:** Human Founder
- **Proposed Remediation:** Submit FashXStudio consent architecture, data retention policy, and privacy policy to qualified technology legal counsel for formal review.
- **Dependencies:** Legal counsel engagement.
- **Acceptance Criteria:** Written legal opinion approving consent mechanisms and data processing agreements prior to pilot user recruitment.
- **Status:** OPEN
- **Created Date:** 2026-11-11 | **Last Reviewed:** 2026-11-11
