# 08 — Recommendation Decision Policy

## Deterministic Evaluation Pipeline

1. Reject any VTO/try-on external evidence immediately (`FitEvidenceSecurityError`).
2. Load versioned `CategoryFitPolicy`; verify `enabled == True`.
3. Verify offer/source permissions, takedown flags, and explicit shopper consents (`fit_profile_storage` + `fit_recommendation_processing`).
4. Validate chart ownership isolation, measurement basis (`BODY` vs approved `GARMENT`), freshness windows, and field completeness (`validate_evidence`).
5. Compute internal evidence score and apply `may_recommend` gate.
6. Evaluate all merchant variants cleanly (`recommend_size`):
   - `0` matching available variants → `NO_AVAILABLE_SIZE` (`NO_MATCHING_SIZE`).
   - `1` matching available variant → `RECOMMENDED` (`WITHIN_PUBLISHED_RANGE`, `ALL_REQUIRED_MEASUREMENTS_MATCH`).
   - `> 1` matching available variants → `POSSIBLE_ALTERNATIVES` (`MULTIPLE_SIZES_MATCH`), never choosing arbitrarily by numeric proximity.
7. Generate explanations and persist an immutable snapshot in `fit_recommendations`.
