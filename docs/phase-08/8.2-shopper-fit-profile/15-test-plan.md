# 15 — Test Plan & Automated Coverage

## Test Suites

- `tests/unit/profile/test_fit_policy_and_definitions.py`: Covers `FITP-REQ-001..004`, `FITP-GUI-001..002`.
- `tests/unit/profile/test_fit_schemas_units_validation.py`: Covers `FITP-SCH-001..005`, `FITP-MAN-001..005`, `FITP-UNT-001..004`, `FITP-RNG-001..004`.
- `tests/unit/profile/test_fit_preferences_and_brand_independence.py`: Covers `FITP-PREF-001..003`, `FITP-CAT-001..005`, `FITP-BRD-001..003`.
- `tests/unit/profile/test_fit_profile_service_history_privacy.py`: Covers `FITP-TS-001..004`, `FITP-UPD-001..005`, `FITP-SEC-001..006`, `FITP-REC-001..002`.
- `tests/unit/profile/test_fit_profile_api.py`: Covers mounted FastAPI routes, OpenAPI parity, RBAC/ownership, optimistic locking 409, and consent 403.
- `mobile/__tests__/fit_profile.test.tsx`: Covers `fitProfileApi`, `useFitProfileStore.clearProfile`, `MeasurementGuidanceCard`, `MeasurementInput`, and `FitPreferenceSelector`.

Master runner: `python -u tests/unit/profile/run_all_fit_profile_tests.py`.
