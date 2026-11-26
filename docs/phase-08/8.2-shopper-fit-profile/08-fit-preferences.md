# 08 — Default Fit Preferences

## 1. Preference Model

Default fit preference captures subjective comfort preference (`SLIM`, `REGULAR`, `RELAXED`, `OVERSIZED`, `NO_PREFERENCE`).

## 2. Invariants

1. Default fit preference starts at `NO_PREFERENCE` (never silently assumes `REGULAR`).
2. Shoppers can set, change, or reset `default_fit_preference` without providing body measurements (`PUT /api/v1/profile/fit/preferences`).
3. Fit preference is subjective; it never modifies merchant size charts and cannot stand in as proof of physical fit.
