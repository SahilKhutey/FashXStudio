# RC12: Step-by-Step Execution Guide

## Step 0: Baseline & Dependency Verification
1. Verify `main` commit SHA and branch state.
2. Confirm that RC08, RC10, and RC11 code modules are present on their respective recovery branches.
3. Review `docs/release/gates.md` and confirm that unverified gates remain flagged as `HOLD` / `UNKNOWN`.

## Step 1: Branch Management
- Branch: `recovery/rc12-productization-public-beta`
- Base: `recovery/rc11-controlled-beta-pilot` (carries forward release configuration, timing, evaluators, and pilot tooling).

## Step 2: Implementation Sequence
1. Implement [`backend/fashx/core/release_policy.py`](file:///c:/Users/ASUS/Documents/FashXStudio/backend/fashx/core/release_policy.py) with deterministic rollout assignment and fail-closed capability decisions.
2. Implement [`scripts/rc12/beta_gates.py`](file:///c:/Users/ASUS/Documents/FashXStudio/scripts/rc12/beta_gates.py) with G1–G6 verification checks.
3. Implement [`scripts/rc12/catalog_health.py`](file:///c:/Users/ASUS/Documents/FashXStudio/scripts/rc12/catalog_health.py) for supply monitoring.
4. Implement [`scripts/rc12/vto_cost_report.py`](file:///c:/Users/ASUS/Documents/FashXStudio/scripts/rc12/vto_cost_report.py) for spend and quota accounting.
5. Author unit, integration, release, and security test suites.

## Step 3: Verification & Staged Launch
1. Run full test suites and static analysis (`docs_lint.py`, `ruff check .`, `mypy .`).
2. Verify that mock try-on cannot be dispatched as real inference in production.
3. Commit and push to `origin recovery/rc12-productization-public-beta`.
4. Open PR targeting `main`.
5. Maintain public registration flag `public_registration.enabled = False` until human founder signs public beta release authorization.
