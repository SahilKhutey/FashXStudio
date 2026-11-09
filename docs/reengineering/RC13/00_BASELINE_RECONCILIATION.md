# RC13: Baseline Reconciliation Across Recovery Cycles

## 1. Repository State Reconciled
- **Main Branch Baseline**: SHA `9e555dadec2a9d85b21bcfdbb95854f3ab17d214` (RC07 Catalog Personalization merged via PR #29).
- **RC08 Staging & Pilot Readiness**: [PR #30](https://github.com/SahilKhutey/FashXStudio/pull/30) (`18c7376`) completely green across all 10 automated CI checks; awaiting founder merge.
- **RC10 Product Optimization**: Commit `d944b29` on branch `origin/recovery/rc10-product-optimization` (29 tests passing).
- **RC11 Beta Pilot Scaffolding**: Commit `516140e` on branch `origin/recovery/rc11-controlled-beta-pilot` (15 tests passing).
- **RC12 Productization & Public Beta**: Commit `20b7d8a` on branch `origin/recovery/rc12-productization-public-beta` (18 tests passing).
- **RC13 Market Readiness**: Branch `recovery/rc13-final-market-readiness` builds upon RC12.

## 2. Threshold Reconciliation (G6 vs Pilot Plan)
Across repository history, two release threshold definitions existed:
1. `docs/release/gates.md`:
   - G6 Cohort: 20–40 real users.
   - Quality standard: >= 75% acceptable try-on ratings.
2. `docs/pilot/pilot-plan.md`:
   - Pre-registered sample: 40–50 activated users.
   - Metrics: M1 (activation >= 70%), M2 (VTO completion >= 60%), M3 (rating >= 3.5/5.0), M4 (crash-free >= 99%), M5 (0 privacy incidents).

**Reconciliation Policy**:
- For strict public market launch, the higher criteria of [`docs/pilot/pilot-plan.md`](file:///c:/Users/ASUS/Documents/FashXStudio/docs/pilot/pilot-plan.md) (M1–M5 with 40–50 activated users) is required.
- The gate evaluator [`scripts/rc13/evaluate_release_gates.py`](file:///c:/Users/ASUS/Documents/FashXStudio/scripts/rc13/evaluate_release_gates.py) enforces full reviewer signoff and verified real evidence references for all gates G1–G6.

## 3. Evidence Integrity
Per `AGENTS.md` Rule 1 and Rule 2:
- Files in `docs/evidence/`, `docs/provenance.md`, and `docs/release/gates.md` are not created or altered by coding agents.
- Current repository state remains **Pre-Pilot** with gates **Unmeasured** until live founder trials take place.
