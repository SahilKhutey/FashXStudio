# Strategy Evidence Index

**Purpose**: Centralized evidence repository linking all empirical artifacts, operational logs, evaluation rubrics, and gate scorings from Phases 5 through 10. Serves as the single source of empirical truth for the Phase 11 strategic decision memo.

---

## 1. Pilot Performance & Release Gate G6 (Phase 10)

- **Gate G6 Decision Memo**: [`docs/pilot/g6-verdict.md`](../pilot/g6-verdict.md)  
  *Core verdict: CONDITIONAL GO / ADVANCE TO PHASE 11; evaluation of hypotheses H1–H4, 3 successes, 3 risks, and prioritized release backlog.*
- **Pre-Registered Pilot Plan & Criteria**: [`docs/pilot/pilot-plan.md`](../pilot/pilot-plan.md)  
  *Pre-registered sampling quotas, M1–M5 must-haves, S1–S4 should-haves, 7 stop rules, and strict change control policy committed prior to Alpha (`0164eea`).*
- **Final Quantitative Telemetry Report**: [`docs/pilot/pilot-report.md`](../pilot/pilot-report.md)  
  *Aggregated data across 45 invites, 42 logins, 38 activated participants; Wilson 95% confidence intervals, demographic & garment slice evaluations, error code taxonomy, and small-cell suppression (<5).*
- **Qualitative Synthesis & Dropout Analysis**: [`docs/pilot/qualitative-synthesis.md`](../pilot/qualitative-synthesis.md)  
  *Synthesis of 10 interviews (including 2 dropouts) across 10 coded themes, verbatim quotes, and discrepancy analysis of words vs. observed actions.*
- **Pilot Behavioral Observations Log**: [`docs/pilot/observations.md`](../pilot/observations.md)  
  *Daily operational notes across Days 1–28 tracking user actions, repeat loops, and session habits.*
- **Change Control Log**: [`docs/pilot/change-log.md`](../pilot/change-log.md)  
  *Documented hotfixes (OTA v0.10.1, backend v0.10.2, survey v0.10.3) verifying zero modifications to ranker weights or MMR diversity parameters during testing.*
- **Incident & Stop-Rule Monitoring Log**: [`docs/pilot/incidents.md`](../pilot/incidents.md)  
  *Continuous monitoring of all 7 stop rules: 0 privacy breaches, 0 crash spikes, 0 vendor circuit breaker trips, and 2 verified erasure drills.*
- **Mid-Pilot Checkpoint 1 (Day 14)**: [`docs/pilot/checkpoint-1.md`](../pilot/checkpoint-1.md)  
  *Interim funnel leakage analysis, top 5 user friction points, and Wave 3 expansion decision.*
- **Data Closure & Retention Log**: [`docs/pilot/closure-log.md`](../pilot/closure-log.md)  
  *Verification of feature flag deactivation, tester list revocation, and DPDP erasure for 8 requesting participants.*
- **Pilot Retrospective**: [`docs/pilot/retro.md`](../pilot/retro.md)  
  *Analysis of operations, tooling learnings, customer support response, and process improvements.*
- **Pilot Task Log**: [`docs/logs/task-log-phase10-closed-pilot.md`](../logs/task-log-phase10-closed-pilot.md)  
  *Comprehensive build and execution log covering PR 10A, Part 10B, and PR 10C.*

---

## 2. Unit Economics & Commercial Viability

- **Pilot Unit Economics Model**: [`docs/pilot/unit-economics.md`](../pilot/unit-economics.md)  
  *Empirical cost accounting ($2.59/mo infra at pilot scale $\to$ $0.12/mo$ at scale; $0.088/wk variable try-on inference); affiliate revenue sensitivity model (1.5% to 3.8% CR); break-even click analysis.*
- **Automated Cost Queries**: [`scripts/pilot/costs.sql`](../../scripts/pilot/costs.sql)  
  *SQL aggregation for GPU inference spend per user and per high-satisfaction generation ($1.26 per rating $\ge 4$).*

---

## 3. Upstream Foundation & Core Pipelines (Phases 5–9)

- **Phase 5 Real Try-On Scorecard & Task Log**: [`docs/logs/task-log-phase05-real-tryon-path.md`](../logs/task-log-phase05-real-tryon-path.md)  
  *FASHN API adapter validation, 200-pair benchmark, Monk skin tone fairness audit (disparity $\le 10\%$), C2PA watermarking, and draped garment capability gating.*
- **Phase 6 Real Catalog & Provenance Register**: [`docs/logs/task-log-phase06-real-catalog.md`](../logs/task-log-phase06-real-catalog.md)  
  *3,420 catalog garments across partner feeds (FabIndia, Snitch, Westside); 1-command takedown CLI (<15 min SLA); rights and provenance flags.*
- **Phase 7 Discovery & Ranking Evaluation**: [`docs/logs/task-log-phase07-discovery-real-data.md`](../logs/task-log-phase07-discovery-real-data.md)  
  *11-feature vector ranker, constrained MMR, 4-tier relaxation ladder, HNSW 100% recall@300, and 0 hard-rule violations across 200 evaluation personas.*
- **Phase 8 Mobile MVP Architecture**: [`docs/logs/task-log-phase08a-mobile-foundation.md`](../logs/task-log-phase08a-mobile-foundation.md)  
  *Expo SDK 57 (RN 0.86 New Architecture) client; Supabase email OTP; local encrypted storage; MASVS L1 security controls.*
- **Phase 9 Privacy, Security & Release Readiness**: [`docs/logs/task-log-phase09c-security-privacy-and-release-gates.md`](../logs/task-log-phase09c-security-privacy-and-release-gates.md)  
  *OWASP API assessment, DPDP privacy package, outside legal counsel sign-off, CERT-In logging compliance, and Gate G1/G3/G4/G5 clearance.*

---

## 4. Current Repository State

- **Canonical Status**: [`docs/STATUS.md`](../STATUS.md)  
  *Current measured status: 1,429 tests (1,178 MVP backend passing), 23 Alembic migrations, 216 MVP routes, 0 ruff errors, and Gate G6 marked CLEARED.*
