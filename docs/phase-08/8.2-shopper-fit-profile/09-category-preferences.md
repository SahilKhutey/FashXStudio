# 09 — Category-Specific Fit Preferences

## 1. Taxonomy & Precedence (`backend/fashx/profile/preferences.py`)

Supported garment categories:
`TSHIRTS`, `SHIRTS`, `KURTAS`, `TOPS`, `TROUSERS`, `JEANS`, `DRESSES`, `SKIRTS`.

Precedence evaluated deterministically via `resolve_fit_preference`:
1. Explicit category preference in `category_fit_preferences`.
2. Shopper's explicit `default_fit_preference` on `shopper_profiles`.
3. `NO_PREFERENCE`.

Category preferences are stored independently (`uq_category_fit_preferences_user_cat`), never leak across unrelated categories, and unknown category codes are rejected with HTTP 422.
