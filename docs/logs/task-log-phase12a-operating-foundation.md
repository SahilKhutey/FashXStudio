# Task Log: PR 12A — Operating Foundation & Measurement Engine

- **Phase:** Phase 12 (Operate, Learn, and Scale — The First 90 Days)
- **PR:** 12A (Operating Foundation)
- **Branch:** `feat/phase12a-operating-foundation`
- **Date:** October 2026
- **Status:** Complete & Verified

---

## 1. Objectives & Scope

Establish the operating system for the 90 days following Gate 1 / Path B selection:
1. Formalize Path B operational target numbers N1, N2, N3 (`docs/operations/PATH.md`).
2. Build the input/output metrics tree (`docs/operations/metrics.md`).
3. Define privacy-safe standing analyst views (`scripts/operations/views.sql`).
4. Implement a deterministic, salt-based experimentation framework (`backend/fashx/core/experiments.py`, `database/models/experiment.py`, `database/migrations/versions/0024_experiment_exposures.py`, and `tests/unit/test_experiments.py`).
5. Pre-register the first storefront experiment: `widget_cta_v1` (`docs/operations/experiments/widget_cta_v1.md`).
6. Establish production SLOs and an error budget policy (`docs/operations/slo.md`).
7. Formalize the release train and staged rollout runbook (`docs/runbooks/release.md`).
8. Establish the weekly, monthly, and quarterly maintenance cadence (`docs/operations/cadence.md`).
9. Build the statutory DPDP countdown calendar to 14 May 2027 (`docs/operations/compliance-calendar.md`).
10. Set cloud infrastructure cost guardrails, unit cost caps, and circuit breakers (`docs/operations/cost-guardrails.md`).
11. Define B2B support ops, triage playbooks, and abuse handling (`docs/operations/support-ops.md`).

---

## 2. Changes Delivered

### Documentation & Operational Artifacts
- `docs/operations/PATH.md`: Path B B2B Brand-First focus, numbers N1 (Live brands $\ge 4$), N2 (Return reduction $\ge 3.0$ pts), N3 (Net SaaS MRR $\ge ₹75,000$).
- `docs/operations/metrics.md`: Complete North Star metrics tree, leading indicators, conversion funnels.
- `docs/operations/experiments/widget_cta_v1.md`: Pre-registered experiment protocol for PDP CTA optimization.
- `docs/operations/slo.md`: SLIs, SLOs, and 4-tier error budget policy protecting shopper and merchant experiences.
- `docs/runbooks/release.md`: Expand-contract database migrations, 5% $\to$ 25% $\to$ 100% canary rollout, automated rollbacks.
- `docs/operations/cadence.md`: Weekly, monthly, and quarterly engineering and compliance rhythms.
- `docs/operations/compliance-calendar.md`: DPDP Act 2023 milestone countdown to statutory enforcement on 14 May 2027.
- `docs/operations/cost-guardrails.md`: ₹1,25,000/mo spend cap, $\le ₹1.20$ blended cost per try-on, 76% gross margins.
- `docs/operations/support-ops.md`: SLAs, collision resolution playbooks, shopper erasure runbook, and trust & safety filters.

### Engineering & Schema
- `backend/fashx/core/experiments.py`: Deterministic SHA-256 bucketing across active experiment configurations.
- `database/models/experiment.py`: `ExperimentExposure` table with composite unique constraint `uq_user_experiment`.
- `database/models/__init__.py`: Registered and exported `ExperimentExposure`.
- `backend/fashx/application/erasure.py`: Classified `experiment_exposures` in `ACCOUNT_TABLES` for DPDP compliance.
- `database/migrations/versions/0024_experiment_exposures.py`: Alembic migration chaining from `0023_pilot_tables`.
- `scripts/operations/views.sql`: Analyst views (`v_events`, `v_tryon_quality`, `v_tenant_usage`, `v_widget_sessions`, `v_experiment_exposures`).
- `tests/unit/test_experiments.py`: 6 unit tests validating deterministic assignment, split ratios, and registry queries.

---

## 3. Verification & Test Evidence

- **Unit Tests:** `pytest tests/unit/test_experiments.py` $\to$ 6 passed in 1.85s.
- **Erasure Classification:** `pytest tests/integration/test_erasure.py -k test_every_model_table_is_classified` $\to$ Passed.
- **Erasure Pipeline:** `pytest tests/integration/test_erasure.py` $\to$ 3 passed, 2 skipped (db-only).
- **Core Suite:** Full non-db test suite $\to$ 1,178 passed.
