# RC11 — Controlled Beta Pilot & Real-World Evidence

**Status**: PLANNING / GATED  
**Owner**: FashXStudio project owner  
**Branch**: `recovery/rc11-controlled-beta-pilot`  

## Objective
Operationalize the pre-registered FashXStudio closed beta pilot ([`docs/pilot/pilot-plan.md`](file:///c:/Users/ASUS/Documents/FashXStudio/docs/pilot/pilot-plan.md)) and collect verifiable real-world evidence for activation, virtual try-on realism, reliability, privacy trust, retention, feed relevance, and retailer click-through intent.

## Dependencies & Release Gate Prerequisites
- **RC08 Staging & Release Readiness**: Staging database, JWKS auth, private S3, and release configurations verified ([PR #30](https://github.com/SahilKhutey/FashXStudio/pull/30)).
- **RC10 Engineering Optimization**: Catalog quality evaluation, recommendation evaluation, execution timing, and B1–B9 gate engine verified ([`recovery/rc10-product-optimization`](https://github.com/SahilKhutey/FashXStudio/tree/recovery/rc10-product-optimization)).
- **Prerequisite Release Gates**: Gates G1, G3, G4, and G5 must be cleared with dated human evidence cards before participant onboarding.
- **Protocol Discrepancy Resolution**: The governance discrepancy between G6 in `docs/release/gates.md` (20–40 users, 75% acceptable) and `docs/pilot/pilot-plan.md` (40–50 activated users, M1–M5 must-haves, S1–S4 should-haves) must be explicitly resolved by the project owner.

## Scope
- Participant operations, pseudonymous participant codes, and voluntary informed consent.
- Cohort tracking (Alpha: 5 testers; Wave 1: 12–15; Wave 2: 15–20; Optional Wave 3: 10–15).
- Event instrumentation and server-side attribution.
- Feedback surveys, realism ratings, defect tagging, SUS, PMF, and NPS.
- Safety controls, spend alerts, hard stop rules, and emergency kill switches.
- Metric calculation ([`scripts/rc11/evaluate_pilot.py`](file:///c:/Users/ASUS/Documents/FashXStudio/scripts/rc11/evaluate_pilot.py)) and data quarantine ([`scripts/rc11/validate_pilot_data.py`](file:///c:/Users/ASUS/Documents/FashXStudio/scripts/rc11/validate_pilot_data.py)).
- Final GO / FIX / HOLD / PIVOT review.

## Out of Scope
- FashX-owned checkout, payment processing, fulfillment, or returns.
- Unlicensed catalog feeds or unauthorized garment images.
- Ranker weight changes or onboarding experiment alterations during Weeks 2–3.
- Mock VTO represented as real AI inference.
- Public launch or unrestricted registration.

## Strict Rules
1. Missing evidence is evaluated as **UNKNOWN**, never as PASS.
2. Simulated, synthetic, or test records are strictly quarantined and never entered into real pilot results.
3. No participant PII, raw photos, or body measurements enter analytics.
4. Hard stop rules override all average ratings and conversion metrics.
5. All pilot modifications are versioned and logged.
6. A `GO` decision requires human founder authorization.

## Document Directory
- [`00_BASELINE_AND_AUTHORIZATION.md`](file:///c:/Users/ASUS/Documents/FashXStudio/docs/reengineering/RC11/00_BASELINE_AND_AUTHORIZATION.md)
- [`01_PILOT_PROTOCOL.md`](file:///c:/Users/ASUS/Documents/FashXStudio/docs/reengineering/RC11/01_PILOT_PROTOCOL.md)
- [`02_PARTICIPANT_OPERATIONS.md`](file:///c:/Users/ASUS/Documents/FashXStudio/docs/reengineering/RC11/02_PARTICIPANT_OPERATIONS.md)
- [`03_EVENT_INSTRUMENTATION.md`](file:///c:/Users/ASUS/Documents/FashXStudio/docs/reengineering/RC11/03_EVENT_INSTRUMENTATION.md)
- [`04_FEEDBACK_AND_SURVEYS.md`](file:///c:/Users/ASUS/Documents/FashXStudio/docs/reengineering/RC11/04_FEEDBACK_AND_SURVEYS.md)
- [`05_SAFETY_AND_INCIDENTS.md`](file:///c:/Users/ASUS/Documents/FashXStudio/docs/reengineering/RC11/05_SAFETY_AND_INCIDENTS.md)
- [`06_METRIC_DEFINITIONS.md`](file:///c:/Users/ASUS/Documents/FashXStudio/docs/reengineering/RC11/06_METRIC_DEFINITIONS.md)
- [`07_EVIDENCE_AND_PROVENANCE.md`](file:///c:/Users/ASUS/Documents/FashXStudio/docs/reengineering/RC11/07_EVIDENCE_AND_PROVENANCE.md)
- [`08_ANALYSIS_AND_DECISION.md`](file:///c:/Users/ASUS/Documents/FashXStudio/docs/reengineering/RC11/08_ANALYSIS_AND_DECISION.md)
- [`09_EXECUTION_GUIDE.md`](file:///c:/Users/ASUS/Documents/FashXStudio/docs/reengineering/RC11/09_EXECUTION_GUIDE.md)
- [`10_TEST_PLAN.md`](file:///c:/Users/ASUS/Documents/FashXStudio/docs/reengineering/RC11/10_TEST_PLAN.md)
- [`11_ACCEPTANCE_REPORT.md`](file:///c:/Users/ASUS/Documents/FashXStudio/docs/reengineering/RC11/11_ACCEPTANCE_REPORT.md)
- [`tasks/RC11_TASK_LIST.md`](file:///c:/Users/ASUS/Documents/FashXStudio/docs/reengineering/RC11/tasks/RC11_TASK_LIST.md)
