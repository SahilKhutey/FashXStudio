# Phase 08 Integration Matrix

| Integration Boundary | Contract / Adapter | Verified Behavior |
|---|---|---|
| Size Chart -> Fit Engine | `ProductSizeChartResponse` + `MerchantSizeOption` | Preserves merchant chart revision, measurement basis, and unit normalization |
| Fit Profile -> Fit Engine | `FitProfileService` + `MeasurementValue` | Enforces `FIT_PROFILE_STORAGE` consent and measurement revision traceability |
| Fit Engine -> VTO Separation | `get_presentation_policy` + `fit_guaranteed=False` | VTO disclaimers explicitly separate visual try-on from physical fit |
| Feedback Loop -> Ranking | `build_shopper_feedback_projection` + `build_product_feedback_feature` | Explicit `DISLIKE`/`LIKE` outweigh passive clicks; consent withdrawal clears projections |
| Ranking Eligibility Gate | `evaluate_eligibility` | Excludes takedowns, out-of-stock, stale, and unpermitted products before scoring |
| User Erasure | `backend/fashx/application/erasure.py` | All Phase 08 user-linked tables classified under `ACCOUNT_TABLES` |
