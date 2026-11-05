# RC07 — Feedback Collection & User Isolation Pipeline

## 1. Objective
Ensure that user feedback signals (`like`, `hide`, `not_interested`) are collected transactionally with strict user isolation, immediate cache invalidation, and prevention of cross-user signal contamination.

## 2. API Endpoint Specification
- **Route**: `POST /api/v1/feed/signals`
- **Security**: JWT Bearer token required (`Principal`).
- **Request Body**:
```json
{
  "garment_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "action": "like"
}
```
- **Response Body**:
```json
{
  "status": "recorded",
  "user_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "garment_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "action": "like"
}
```

## 3. Database Invariants
- Table `feed_signals` (`database/models/feed.py`):
  - Primary Key: `(user_id, garment_id, action)`
  - Check Constraint: `ck_feed_signal_action` restricts `action IN ('like', 'hide', 'not_interested')`.
  - Owned-resource guarantee: `user_id` is extracted strictly from the verified JWT `principal.user_id`. Clients cannot pass or alter another user's `user_id`.
  - Invalidation: `invalidate_user_cache(user_id)` is invoked immediately upon signal write to ensure subsequent feed calls reflect user feedback.

## 4. Verification
Integration test `tests/integration/test_rc07_feedback_pipeline.py` verifies:
- Recording `like`, `hide`, `not_interested` with valid JWT.
- Immediate 401/403 rejection without valid JWT.
- Schema validation rejection (400/422) for unsupported action strings.
- Cross-user isolation: User A and User B recording signals on the same garment produce separate records without collision.
