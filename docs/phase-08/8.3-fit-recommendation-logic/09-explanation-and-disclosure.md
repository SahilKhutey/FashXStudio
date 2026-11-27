# 09 — Explanation, Disclosure & Language Guard

## Approved Reason Mapping (`explanations.py`)

Machine-readable `FitReasonCode` values map strictly to reviewed plain-language copy (`EXPLANATIONS`):
- `WITHIN_PUBLISHED_RANGE`
- `ALL_REQUIRED_MEASUREMENTS_MATCH`
- `MULTIPLE_SIZES_MATCH`
- `MISSING_REQUIRED_MEASUREMENT`
- `NO_MERCHANT_CHART`
- `CHART_BASIS_UNSUPPORTED`
- `PREFERENCE_NOT_EVALUATED`
- `CATEGORY_NOT_VALIDATED`
- `NO_MATCHING_SIZE`
- `STALE_CHART`, `STALE_SHOPPER_MEASUREMENT`, `CHART_CONFLICT`, `PERMISSION_INVALID`, `VARIANT_UNAVAILABLE`, `EASE_POLICY_MISSING`, `EASE_WITHIN_POLICY`, `OUTSIDE_EASE_POLICY`

## Anti-Guarantee Policy

Every recommendation returns `fit_guaranteed: false`, `disclaimer_code: "SIZE_GUIDANCE_NOT_FIT_GUARANTEE"`, and runs `assert_no_guarantee_language` to reject phrases such as `"guaranteed to fit"`, `"100% accurate"`, or `"verified physical fit"`. Mobile renders `<FitDisclaimer />` separately from Visual Try-On.
