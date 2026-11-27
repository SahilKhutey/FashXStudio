# 16 — Automated & Staging Test Plan

## Backend Automated Suites (`tests/unit/fit/`)

- **Matcher, Category Policy & Ease (`test_fit_matcher_and_policy.py`)**: exact inclusive Decimal boundaries, mismatched field/width rejection, `TSHIRTS` vs disabled `TROUSERS`/`SAREES`/unknown categories, `GARMENT` rejection without `EaseRule`, and `EasePolicyRegistry` evaluation.
- **Evidence, Confidence, Decision & Explanations (`test_fit_evidence_confidence_decision.py`)**: Merchant A vs B isolation, chart revision invalidation, missing chest (height/weight-only blocked), missing/stale/unknown-basis charts, optional measurement non-blocking, confidence dimension bounds & hard-gate precedence, `POSSIBLE_ALTERNATIVES`, `NO_AVAILABLE_SIZE`, VTO rejection, and guarantee-language guard.
- **Evaluation & Feedback (`test_fit_feedback_and_evaluation.py`)**: dataset loading, split leakage errors, empty dataset rejection, selective metrics, calibration bins, small-sample warnings, feedback ownership (`PermissionError`), missing recommendation (`KeyError`), unverified vs physical basis, duplicate rejection, triage without rule mutation, and shopper deletion.
- **API & Auth (`test_fit_api.py`)**: OpenAPI route mounting with `get_principal`, `extra="forbid"` client spoofing rejection, owner snapshot & feedback retrieval, cross-shopper `403`.

## Mobile Suite (`mobile/__tests__/fit_recommendation.test.tsx`)

- API client calls, recommended size rendering without uncalibrated score percentages, abstention states (`INSUFFICIENT_INFORMATION`, `POSSIBLE_ALTERNATIVES`), loading/error retry, and feedback submission.
