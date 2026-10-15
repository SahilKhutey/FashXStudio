> **Development log. Contains no real-world measurements.**

# Task Log: Phase 10A — Pilot Tooling, Alpha & Launch Readiness

**Date**: 2026-10-12  
**Status**: COMPLETED  
**Branch**: `feat/phase10a-pilot-tooling`  

---

## 1. Summary of Deliverables

Phase 10A establishes the pre-registered testing protocol, backend endpoints, database models, cohort tracking, analytics views, and operations kit for the closed 40–50 person pilot:

1. **Pre-Registered Pilot Plan (`docs/pilot/pilot-plan.md`)**:
   - Sample & cohort definition (Alpha: 5, Wave 1: 12–15, Wave 2: 15–20, Wave 3: 10–15).
   - Coverage targets: size diversity (S, M, L, XL+), phone platforms (Android + ≥10 iPhones), ≥50% non-friend participants, ≥5 ethnic-wear shoppers, non-metro representation.
   - Core hypotheses (H1 to H4).
   - Pre-registered Gate G6 criteria: 5 Must-Haves (M1–M5) and 4 Should-Haves (S1–S4) with frozen thresholds.
   - Hard stop rules and change control governance.

2. **Database Migration & Models (`0023_pilot_tables.py`)**:
   - `pilot_invites`: Single-use codes storing only SHA-256 hashes.
   - `pilot_participants`: Cohort attribution and platform metadata without PII.
   - `pilot_survey_responses`: Unique constraint enforcing one submission per survey key per user.
   - `pilot_feedback`: Categorized feedback with sanitized context.
   - Table classification guard updated in `backend/fashx/application/erasure.py`.

3. **Backend Pilot Endpoints (`backend/fashx/pilot/router.py`)**:
   - `POST /pilot/join`: Atomically redeems single-use invite code with `FOR UPDATE` lock; returns uniform 404 for invalid and already-used codes.
   - `POST /pilot/feedback`: Ingests user feedback with strict context key allowlisting (`screen`, `app_version`, `job_id`).
   - `GET /pilot/surveys/pending`: Evaluates user activity to schedule `tryon_first` (post-tryon), `feed_day5` (day 5), or `end_of_pilot` (when flag is set).
   - `POST /pilot/survey`: Validates responses against strict Pydantic schemas (`TryonFirst`, `FeedDay5`, `EndOfPilot`) with `extra="forbid"`; returns 409 Conflict on repeat submissions.

4. **Pseudonymous Views & Reporting Kit (`scripts/pilot/`)**:
   - `views.sql`: Generates salted views (`v_pilot_events`, `v_pilot_tryon_jobs`, `v_pilot_feed_impressions`, etc.) hashing `user_id` with an internal salt and omitting free-text columns.
   - `funnel.sql` & `retention.sql`: Calculates activation, time-to-first-tryon, and day 0–6 vs day 7–13 retention.
   - `tryon_quality.sql`, `feed_quality.sql`, `costs.sql`: Monitors latency, completion, defect rate, and daily inference spend.
   - `pilot_report.py`: Implements Wilson 95% confidence intervals and small-cell suppression (`<5`).

5. **Operations & Participant Materials**:
   - `docs/pilot/templates.md`: Plain-language email and messaging templates.
   - `docs/pilot/participant-one-pager.md`: 1-page onboarding and privacy guide.
   - `docs/pilot/support-playbook.md`: Standard operating procedures for the top 10 support scenarios.
   - `docs/pilot/interview-guide.md`: 30-minute qualitative interview protocol.
   - `docs/pilot/known-issues.md`: Live known-issues tracking.
   - `docs/pilot/alpha-log.md`: 5-person alpha rehearsal documenting support, erasure, and kill switch drills.
   - `docs/pilot/launch-checklist.md`: Signed launch readiness checklist.

---

## 2. Test Verification Summary

- `tests/unit/test_pilot.py`: 5/5 PASSED (Invite hashing, survey validation schemas, context sanitization, cascading erasure).
- `tests/security/test_pilot_endpoints.py`: 3/3 PASSED (Default deny, 404 secrecy, 409 conflict checks).
- `tests/integration/test_erasure.py`: PASSED (Table classification guard verified across all models).
