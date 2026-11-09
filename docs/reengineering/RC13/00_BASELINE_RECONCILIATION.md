# RC13: Baseline Reconciliation & Governance Contract

## 1. Merged Repository State (Post-Merge Audit Baseline)
- **Main Branch Head**: Commit `050b504` on `main`.
- **Merged Pull Requests**:
  - [PR #30](https://github.com/SahilKhutey/FashXStudio/pull/30): RC08 Staging, security & pilot readiness — **MERGED**
  - [PR #31](https://github.com/SahilKhutey/FashXStudio/pull/31): RC11 Controlled beta pilot scaffolding — **MERGED**
  - [PR #32](https://github.com/SahilKhutey/FashXStudio/pull/32): RC12 Productization & release policy governance — **MERGED**
  - [PR #33](https://github.com/SahilKhutey/FashXStudio/pull/33): RC13 Final market readiness framework — **MERGED**
- **Crucial Governance Invariant**: Merged code is **not** real-world validation. Software integration is complete across all recovery cycles, but release gates G1–G6 remain evaluated as **Unmeasured / HOLD** until authentic human evidence cards are produced by the founder from real trials.

## 2. Authoritative Metric Contract (Reconciled to Frozen Pilot Plan)
The historical discrepancy between `docs/release/gates.md` and `docs/pilot/pilot-plan.md` is resolved by adopting [`docs/pilot/pilot-plan.md`](file:///c:/Users/ASUS/Documents/FashXStudio/docs/pilot/pilot-plan.md) as the **single authoritative contract**:

### Must-Have Criteria (M1–M5 — 100% Required for "GO")
- **M1 (Activation)**:
  - $\ge 60\%$ of login invitees complete onboarding with an accepted body photo (`M1_login_invitee_completion_rate >= 0.60`).
  - $\ge 80\%$ of onboarding starters complete onboarding (`M1_onboarding_starter_completion_rate >= 0.80`).
- **M2 (Try-on Realism)**:
  - Mean user rating $\ge 3.80 / 5.0$ (`M2_mean_vto_rating >= 3.80`).
  - $\ge 70\%$ of ratings are 4 or 5 (`M2_ratings_gte_4_rate >= 0.70`).
  - $\le 15\%$ defect flags (`M2_defect_rate <= 0.15`).
- **M3 (Reliability)**:
  - $\ge 99.0\%$ crash-free mobile sessions (`M3_crash_free_sessions >= 0.99`).
  - $\ge 90.0\%$ try-on completion rate (`M3_tryon_success_rate >= 0.90`).
  - P95 end-to-end latency $\le 45.0$ seconds (`M3_p95_latency_seconds <= 45.0`).
- **M4 (Trust & Privacy)**:
  - Exactly $0$ security or privacy incidents (`M4_privacy_incident_count <= 0`).
  - $\ge 80\%$ agreement on photo comfort survey (`M4_photo_comfort_agreement_rate >= 0.80`).
  - $\le 10\%$ consent screen abandonment (`M4_consent_dropoff_rate <= 0.10`).
- **M5 (Return / Retention)**:
  - $\ge 50\%$ week-2 return rate (`M5_week2_return_rate >= 0.50`).

### Should-Have Criteria (S1–S4 — At Least 3 of 4 Groups Required)
- **S1 (Feed Relevance)**: $\ge 60\%$ survey ratings $\ge 4/5$, $\le 15\%$ negative signals.
- **S2 (Engagement)**: $\ge 60\%$ try-on in Week 1, Median $\ge 3$ try-ons/user, Median $\le 10$ min to first try-on.
- **S3 (Purchase Intent)**: $\ge 40\%$ click "Buy on Store", $\ge 3$ verified purchases reported.
- **S4 (Satisfaction)**: SUS score $\ge 68$, PMF "very disappointed" $\ge 30\%$, NPS $\ge 20$.

## 3. VTO Standard Reconciliation (Gate Ceiling vs. Target)
- **Contractual Gate Ceiling**: Completion $\ge 90.0\%$, Defect $\le 15.0\%$, P95 Latency $\le 45.0$s, Mean Rating $\ge 3.80$.
- **Operational Excellence Target**: Completion $\ge 95.0\%$, Defect $\le 10.0\%$, P95 Latency $\le 30.0$s, Mean Rating $\ge 4.00$.

## 4. Evidence Authentication Standards
- An evidence card must have an existing `source_file` on disk.
- Its SHA-256 checksum must match the actual file bytes.
- Placeholders (`unassigned`, `test`, `dummy`) are rejected.
- Future timestamps are rejected.
