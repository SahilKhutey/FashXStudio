# Phase 08.5 Consent & Privacy Controls

- Distinct consent purposes: `ESSENTIAL_SERVICE`, `PERSONALIZED_RANKING`, `PRODUCT_ANALYTICS`, `VTO_THIRD_PARTY_PROCESSING`, `FIT_PROFILE_PROCESSING`, `FEEDBACK_EVALUATION`, `MODEL_TRAINING`.
- Withdrawing `PERSONALIZED_RANKING`:
  1. Appends a `WITHDRAWN` revision to `shopper_consent_records`.
  2. Immediately blocks new personalization event collection and processing (`SKIPPED`).
  3. Clears personalization projections and invalidates the shopper's Phase 08.4 ranking cache.
  4. Leaves `build_shopper_feedback_projection` returning `{}` so ranking falls back to neutral defaults / baseline behavior.
- All new user-linked tables are classified under `ACCOUNT_TABLES` in `backend/fashx/application/erasure.py`.
