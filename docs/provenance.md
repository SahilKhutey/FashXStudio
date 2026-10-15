# Data & Metrics Provenance Register

_Source of truth for data provenance and measurement verification. Every metric or claim in documentation must be listed here. A row without verifiable raw data is marked **Unverified**._

| Metric / Claim | Published Value | Location in Docs | Source / Instrument | Collected By | Date | Raw Data Location | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Backend Unit Tests** | 1,193 passed, 244 frozen | `docs/STATUS.md` | Pytest CI run 38350544833 | GitHub Actions CI | 2026-10-13 | GitHub Actions Run 38350544833 | **Verified** |
| **Mobile Tests** | 7 passed (jest) | `docs/STATUS.md` | Jest CI run 38350544833 | GitHub Actions CI | 2026-10-13 | `mobile/__tests__/` | **Verified** |
| **Database Migrations** | 25 migrations, head 0025 | `docs/STATUS.md` | Alembic `heads` | Alembic CLI | 2026-10-13 | `database/migrations/` | **Verified** |
| **Lint & Type Safety** | 0 ruff errors, 0 mypy issues | `docs/STATUS.md` | Ruff & Mypy CI jobs | GitHub Actions CI | 2026-10-13 | GitHub Actions Run 38350544833 | **Verified** |
| **Mobile Bundle Size** | 3.5 MB Android HBC | `docs/evidence-audit.md` | `npx expo export --platform android` | Metro Bundler | 2026-10-15 | `mobile/dist/_expo/static/js/android/` | **Verified** |
| **Pilot Participants** | 38 users, 45 invites | `_simulated/pilot/` | Simulated template | Assistant | 2026-10-12 | None | **Unverified (Rehearsal)** |
| **Pilot Realism Score** | 4.12 / 5.0 | `_simulated/pilot/` | Simulated template | Assistant | 2026-10-12 | None | **Unverified (Rehearsal)** |
| **Gate 2 Brand MRR** | ₹95,000 contracted MRR | `_simulated/operations/`| Simulated template | Assistant | 2026-10-12 | None | **Unverified (Rehearsal)** |
| **Return Rate Reduction**| 3.4 percentage points | `_simulated/operations/`| Simulated template | Assistant | 2026-10-12 | None | **Unverified (Rehearsal)** |
| **Restore Drill RTO** | 1h 2m RTO | `_simulated/release/` | Simulated template | Assistant | 2026-10-11 | None | **Unverified (Rehearsal)** |
| **Legal Counsel Sign-off**| Approved without reservations | `_simulated/release/` | Simulated template | Assistant | 2026-10-11 | None | **Unverified (Rehearsal)** |
| **Try-on Latency (P95)** | 6.4s / 14.1s | `_simulated/release/` | Simulated template | Assistant | 2026-10-11 | None | **Unverified (Rehearsal)** |
| **Marginal Cost/Try-on** | ₹1.14 / $0.065 | `_simulated/pilot/` | Simulated model | Assistant | 2026-10-12 | None | **Unverified (Rehearsal)** |
