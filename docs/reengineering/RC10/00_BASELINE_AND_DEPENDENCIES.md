# RC10-A: Baseline, Evidence & Dependency Reconciliation

## 1. Repository Reality Check
An inspection of the repository baseline confirms the actual state:
- **`main` SHA**: `9e555dadec2a9d85b21bcfdbb95854f3ab17d214` (PR #29 merged).
- **RC08 Pull Request**: PR #30 (`recovery/rc08-staging-pilot-readiness` commit `18c7376`) has completed all CI checks with 100% success; awaits founder merge.
- **RC09 Pilot Status**: No RC09 branch or real-world user cohort was found. The project remains explicitly pre-pilot as specified in `README.md` and `docs/STATUS.md`.
- **Release Gates (G1–G6 / B1–B9)**: Unmeasured or held pending live human participant verification. Under `AGENTS.md` Rule 1 and Rule 2, no simulated evidence is substituted.

## 2. Track Architecture
To maintain absolute compliance with project governance and engineering rigor, RC10 operates across two distinct tracks:
1. **Track A — Engineering Tooling & Release Invariants**:
   - Automated catalog quality evaluation (`scripts/rc10/evaluate_catalog.py`).
   - Mathematically verified ranking evaluation (`scripts/rc10/evaluate_recommendations.py`).
   - Conservative, fail-closed beta release gate evaluation (`scripts/rc10/beta_gates.py`).
   - Strict metric schema and evidence classification validation (`scripts/rc10/validate_metrics.py`).
   - Latency profiling and reporting tools (`backend/fashx/core/rc10_timing.py`, `scripts/rc10/summarize_performance.py`, `scripts/rc10/generate_acceptance_report.py`).
2. **Track B — Real-World Evidence & Validation**:
   - Real participant acquisition and consent.
   - External catalog partner authorization and rights clearance.
   - Live cloud infrastructure deployment (PostgreSQL, Redis, Supabase JWKS, S3).
   - Real VTO provider API benchmarking and billing reconciliation.
   - Physical mobile device QA across Android and iOS hardware.

## 3. Evidence Classification
Under `validate_metrics.py`, evidence is categorized into:
- `real`: Verified human users, live partner feeds, and authentic production API executions. Required for all official release claims.
- `synthetic`: Algorithmic fixture models and mock vectors used for CI and regression testing.
- `simulated`: Architectural dry-runs and rehearsal pipelines; ineligible for pilot or gate passage.
- `test`: Automated unit, integration, and security test harnesses.
