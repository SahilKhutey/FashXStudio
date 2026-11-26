# 10 — Brand-Size Independence Policy

## 1. Non-Equivalence Invariant

A shopper's measurement profile or declared size at Brand A (`M`) must never be converted into Brand B's size label without:
1. An active product-specific merchant size chart (Phase 08.1).
2. Explicit chart measurement basis (`BODY` or `GARMENT`).
3. Required shopper body measurements from `CATEGORY_POLICIES`.

## 2. Guard Enforcement

`ensure_no_brand_size_assumption` raises `BrandSizeMappingError("INSUFFICIENT_DATA...")` whenever any prerequisite is absent. Historical size labels (`profile_category_sizes`) remain separated from subjective fit preferences (`category_fit_preferences`) and physical measurements (`profile_measurements`).
