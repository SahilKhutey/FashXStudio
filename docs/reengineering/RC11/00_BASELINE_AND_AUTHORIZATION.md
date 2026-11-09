# RC11: Baseline and Pilot Authorization Record

## 1. Baseline Repository State
- **Main SHA**: `9e555dadec2a9d85b21bcfdbb95854f3ab17d214` (PR #29 merged).
- **RC08 Staging PR**: [PR #30](https://github.com/SahilKhutey/FashXStudio/pull/30) (`18c7376`) verified 100% green; awaiting founder merge on GitHub.
- **RC10 Engineering Optimization**: Branch `recovery/rc10-product-optimization` (`d944b29`) created, tested (29 tests passed), and pushed to remote origin.
- **Pilot Plan Status**: [`docs/pilot/pilot-plan.md`](file:///c:/Users/ASUS/Documents/FashXStudio/docs/pilot/pilot-plan.md) is pre-registered and frozen.

## 2. Governance Discrepancy Reconciliation
A discrepancy exists between historical release documentation and the pre-registered plan:
- **`docs/release/gates.md` (Gate G6)**: Summarizes 20–40 participants and ≥75% acceptable try-on realism.
- **`docs/pilot/pilot-plan.md` (Frozen Protocol)**: Requires 40–50 activated users (60–70 invites), all 5 Must-Haves (M1–M5), and at least 3 of 4 Should-Haves (S1–S4).

**Resolution Directive**: Under `AGENTS.md` Rule 1, coding agents must not alter `docs/release/gates.md`. The frozen protocol in `docs/pilot/pilot-plan.md` governs operational execution. The project owner must sign off on this discrepancy before participant recruitment begins.

## 3. Pilot Authorization Record

```
Pilot ID: fashx-closed-beta-01
Repository Base SHA: 9e555da
RC11 Branch: recovery/rc11-controlled-beta-pilot
Release Candidate Version: v0.9-pilot-ready
Authorization Date: PENDING
Approval Owner: Human Project Founder
Independent Reviewer: PENDING
```

### Pre-Authorization Checklist

| Prerequisite | Required Verification | Status | Evidence Reference |
| :--- | :--- | :--- | :--- |
| **RC08 Staging Baseline** | Cloud DB, JWKS auth, private S3, CI workflow | 🟢 VERIFIED (Code/CI) | PR #30 (`18c7376`) |
| **RC10 Optimization** | Catalog evaluator, recs metrics, beta gates | 🟢 VERIFIED (Code/CI) | Branch `d944b29` |
| **Gate G1 (Real-Stack Journey)** | Clean DB deploy, user profile, catalog feed | 🟡 UNVERIFIED | Pending live Postgres run |
| **Gate G3 (VTO Quality & SLA)** | Real provider key, P95 ≤ 45s, fail-closed validation | 🟡 UNVERIFIED | Pending live vendor API run |
| **Gate G4 (Privacy & Recovery)** | Erasure tombstones, signed URLs, GDPR/DPDP | 🟢 VERIFIED (Code/Tests)| `test_rc10_privacy_regression.py` |
| **Gate G5 (Catalog Rights)** | Commercial partner authorization, no scraping | 🟡 UNVERIFIED | Pending commercial partner agreement |
| **Kill Switches Tested** | Emergency stop `tryon_enabled=False`, rollout pause | 🟢 VERIFIED (Code/Tests)| `test_kill_switches.py` |
| **Incident Owner Assigned** | Primary & backup support contacts documented | 🟡 UNVERIFIED | Pending founder assignment |

**Current Authorization Decision**: **`NOT_AUTHORIZED`**  
*No participant invitations may be sent until mandatory release gates G1, G3, G4, and G5 are cleared with human evidence cards and signed by the project founder.*
