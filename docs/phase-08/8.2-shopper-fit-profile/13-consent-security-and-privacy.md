# 13 — Consent, Security & Privacy Controls

## 1. Purpose-Specific Consent

Reuses `ConsentRecord` and `ConsentEvent` via `FitConsentService` (`consent.py`) across four isolated purposes:
- `fit_profile_storage` (required before saving measurements; requires adult `is_18_or_older` check)
- `fit_recommendation_processing`
- `third_party_fit_processing`
- `model_training`

Withdrawing `fit_profile_storage` immediately marks stored measurements `WITHDRAWN`, invalidates cached `FitRecommendation` rows, and blocks subsequent writes.

## 2. Privacy & Zero-PII Logging

- Numeric measurement values are never emitted to application logs (`logger.info` logs field code only) or `profile_audit_events.details_json`.
- Account deletion (`backend/fashx/application/erasure.py`) includes `profile_measurements`, `profile_measurement_history`, `category_fit_preferences`, and `profile_audit_events` in `ACCOUNT_TABLES`.
- Client-supplied shopper IDs are rejected; all queries scope strictly by authenticated `principal.user_id`.
