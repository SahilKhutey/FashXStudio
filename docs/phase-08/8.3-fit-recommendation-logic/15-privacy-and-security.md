# 15 — Privacy, Consent & Security Controls

1. **Authentication & Ownership**: All `/api/v1/fit/*` routes require `get_principal`; `GET` and `POST /feedback` verify ownership (`user_id == principal.user_id`, returning `403` for cross-shopper requests).
2. **Consent Enforcement**: `evaluate_fit_recommendation` verifies both `FIT_PROFILE_STORAGE` and `FIT_RECOMMENDATION_PROCESSING` consents before using shopper measurements.
3. **Zero VTO Evidence Leakage**: `reject_prohibited_evidence` raises `FitEvidenceSecurityError` if any try-on/image source is supplied as fit evidence.
4. **Minimal Snapshot Storage**: `fit_recommendations` and `fit_recommendation_evidence` record source revision references rather than duplicating sensitive body-measurement values across recommendation tables.
5. **Erasure Compliance**: Both `fit_feedback` and `fit_recommendations` are classified in `ACCOUNT_TABLES` (`backend/fashx/application/erasure.py`), verified by `test_every_model_table_is_classified` and `test_erasure_lists_are_disjoint`.
