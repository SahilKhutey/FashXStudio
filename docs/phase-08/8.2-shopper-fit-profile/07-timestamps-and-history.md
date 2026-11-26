# 07 — Timestamps, Optimistic Locking & Measurement History

## 1. Explicit Timestamp Separation

Every row in `profile_measurements` tracks distinct UTC timestamps:
- `measured_at`: When the shopper actually took the measurement (preserved if older measurement entered later).
- `created_at`: When FashXStudio first saved the row.
- `updated_at`: Last mutation timestamp.
- `verified_at`: Set only when a shopper explicitly confirms an aged/unusual measurement remains accurate via `POST /api/v1/profile/fit/measurements/{field}/confirm`.

## 2. Freshness Policy

Measurements whose `verified_at` (or `measured_at` if unconfirmed) exceeds `DEFAULT_MEASUREMENT_STALE_DAYS = 180` automatically surface as `NEEDS_REVIEW` (`needs_confirmation = true`) without deleting stored records.

## 3. Optimistic Locking & Immutable History

- `PATCH /api/v1/profile/fit/measurements/{field}` requires `expected_version`.
- `FitProfileRepository.update_measurement_with_version` executes an atomic SQL `UPDATE ... WHERE id = :id AND user_id = :uid AND version = :expected_version`. Stale versions raise `OptimisticLockConflictError` (HTTP 409).
- Every creation, update, and deletion appends an immutable row to `profile_measurement_history` and invalidates downstream `FitRecommendation` records (`is_valid = False`).
