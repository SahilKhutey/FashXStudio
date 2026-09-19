# AI Fashion Assistant — Production Build Foundation 17

## Try-On Feedback & Learning Instrumentation

Foundation 17 adds the first closed-loop instrumentation layer for the MVP try-on hypothesis.

### Backend

- `POST /api/v1/tryon/{job_id}/feedback`
- `POST /api/v1/tryon/{job_id}/telemetry`
- `tryon_feedback` uniqueness per `(user_id, tryon_job_id)`
- durable `domain_events` for try-on lifecycle events
- lifecycle events: `tryon_started`, `tryon_completed`, `tryon_failed`, `tryon_retry_requested`, `tryon_cancelled`
- user telemetry events: `tryon_viewed`, `tryon_retry_requested`

### Feedback model

Visual feedback is kept separate from physical fit feedback:

- `visual_accuracy`: perceived rendering accuracy
- `purchase_confidence`: 1–5 confidence signal

This prevents model-quality feedback from being confused with physical garment fit outcomes.

### Privacy/data boundary

Only the authenticated user can submit feedback for their own try-on job. Telemetry is restricted to an allowlisted event set and stores only bounded context fields.

### Mobile

The completed try-on screen now:

1. records a result-view event,
2. presents the visual-accuracy feedback control,
3. records retry intent,
4. retains the normal save/buy path.

TanStack Query remains the server-state owner; no analytics or feedback state is stored as a second server-state cache in Zustand.

### Migration

`0011_tryon_feedback_instrumentation` adds the database uniqueness constraint preventing duplicate feedback for the same user/job pair.

### Verification

- Python test suite: 74 passed
- Python compilation: PASS
- Alembic offline chain: PASS
- `git diff --check`: PASS

Mobile TypeScript/Expo runtime verification was not available in this execution environment because dependencies are not installed.
