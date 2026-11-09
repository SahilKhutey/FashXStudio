# RC11: Step-by-Step Pilot Execution Guide

## Step 0: Repository & Dependency Reconciliation
Before launching pilot operations:
1. Verify `main` commit SHA and confirm PR #30 status.
2. Confirm that release gates G1, G3, G4, and G5 have dated evidence cards signed by the human founder.
3. Obtain founder sign-off on the G6 vs `pilot-plan.md` threshold discrepancy.
4. Verify staging environment database (PostgreSQL), Redis queue, JWKS auth, and S3 bucket health.

## Step 1: Branch Management
- Branch: `recovery/rc11-controlled-beta-pilot`
- Base: `recovery/rc10-product-optimization` (contains RC08 `ReleaseConfig` and RC10 evaluation tools).

## Step 2: Data Validation & Dry Run
Before running pilot snapshots:
```bash
# Validate snapshot schema and verify zero PII
python scripts/rc11/validate_pilot_data.py --input path/to/pilot_snapshot.json

# Evaluate snapshot against frozen M1-M5 and S1-S4 rules
python scripts/rc11/evaluate_pilot.py path/to/pilot_snapshot.json
```

## Step 3: Alpha Rehearsal (3 Days)
1. Issue 5 invitations to trusted testers (`P-0001` through `P-0005`).
2. Verify photo capture, guided quality checks, and explicit consent flows.
3. Test emergency kill switch (`tryon_enabled=False`).
4. Rehearse withdrawal and right-to-erasure workflows.
5. Review defects and patch top usability blockers.

## Step 4: Wave 1 & Wave 2 Execution
1. Wave 1: Invite 12–15 participants; monitor telemetry and crash reports.
2. Freeze ranker weights, MMR parameters, and onboarding flow steps.
3. Wave 2: Invite 15–20 participants; measure Day 7–13 retention windows.
4. Optional Wave 3: Invite 10–15 participants if size, platform, or style diversity targets have gaps.

## Step 5: Final Evidence & Review
1. Export immutable raw telemetry manifests.
2. Compute frozen metrics and verify against stop rules.
3. Founder authors evidence cards in `docs/evidence/RC11/`.
4. Conduct independent review and issue signed GO / FIX / HOLD / PIVOT decision.
