# Shopper Profile Test Report

## 1. Test Execution Command and Results

Command executed:
```bash
pytest tests/profile/ -v
```

Command Output:
```
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.1.1, pluggy-1.6.0 -- C:\Users\ASUS\AppData\Local\Programs\Python\Python312\python.exe
hypothesis profile 'default'
rootdir: C:\Users\ASUS\Documents\FashXStudio
configfile: pytest.ini
plugins: anyio-4.12.1, hypothesis-6.156.6, langsmith-0.14.4, asyncio-1.4.0, cov-7.1.0
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collecting ... collected 22 items

tests/profile/test_shopper_profile_api.py::test_get_profile_me_auto_creates_default PASSED [  4%]
tests/profile/test_shopper_profile_api.py::test_put_profile_me_create_or_replace PASSED [  9%]
tests/profile/test_shopper_profile_api.py::test_patch_profile_me_partial_update PASSED [ 13%]
tests/profile/test_shopper_profile_api.py::test_patch_profile_me_clearing_fields PASSED [ 18%]
tests/profile/test_shopper_profile_api.py::test_optimistic_locking_conflict PASSED [ 22%]
tests/profile/test_shopper_profile_api.py::test_feature_completeness_endpoint PASSED [ 27%]
tests/profile/test_shopper_profile_api.py::test_category_sizes_endpoints PASSED [ 31%]
tests/profile/test_shopper_profile_ownership.py::test_shopper_profile_ownership_isolation PASSED [ 36%]
tests/profile/test_shopper_profile_ownership.py::test_disabled_account_blocked PASSED [ 40%]
tests/profile/test_shopper_profile_ownership.py::test_deletion_pending_account_blocked PASSED [ 45%]
tests/profile/test_shopper_profile_ownership.py::test_unauthenticated_request_rejected PASSED [ 50%]
tests/profile/test_shopper_profile_validation.py::test_height_range_validation PASSED [ 54%]
tests/profile/test_shopper_profile_validation.py::test_weight_range_validation PASSED [ 59%]
tests/profile/test_shopper_profile_validation.py::test_physical_attributes_optional PASSED [ 63%]
tests/profile/test_shopper_profile_validation.py::test_controlled_enums_validation PASSED [ 68%]
tests/profile/test_shopper_profile_validation.py::test_style_and_color_preferences_validation PASSED [ 72%]
tests/profile/test_shopper_profile_validation.py::test_shopping_preferences_budget_validation PASSED [ 77%]
tests/profile/test_shopper_profile_validation.py::test_mass_assignment_protection PASSED [ 81%]
tests/profile/test_unit_normalization.py::test_inches_to_cm_standard_values PASSED [ 86%]
tests/profile/test_unit_normalization.py::test_feet_inches_to_cm_standard_values PASSED [ 90%]
tests/profile/test_unit_normalization.py::test_pounds_to_kg_standard_values PASSED [ 95%]
tests/profile/test_unit_normalization.py::test_unit_conversion_invalid_inputs PASSED [100%]

============================= 22 passed in 8.90s ==============================
```

## 2. Regression Test Execution (MVP 2 Auth & Profile)

Command executed:
```bash
pytest tests/unit/test_mvp2_auth_consent_profile.py -v
```

Command Output:
```
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.1.1, pluggy-1.6.0 -- C:\Users\ASUS\AppData\Local\Programs\Python\Python312\python.exe
hypothesis profile 'default'
rootdir: C:\Users\ASUS\Documents\FashXStudio
configfile: pytest.ini
plugins: anyio-4.12.1, hypothesis-6.156.6, langsmith-0.14.4, asyncio-1.4.0, cov-7.1.0
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collecting ... collected 8 items

tests/unit/test_mvp2_auth_consent_profile.py::test_create_profile_binds_to_principal PASSED [ 12%]
tests/unit/test_mvp2_auth_consent_profile.py::test_onboarding_principal_user_uuid_fail_closed PASSED [ 25%]
tests/unit/test_mvp2_auth_consent_profile.py::test_consent_event_audit_logging PASSED [ 37%]
tests/unit/test_mvp2_auth_consent_profile.py::test_mobile_consent_creates_events PASSED [ 50%]
tests/unit/test_mvp2_auth_consent_profile.py::test_get_profile_me_endpoint PASSED [ 62%]
tests/unit/test_mvp2_auth_consent_profile.py::test_update_preferences_budget_validation PASSED [ 75%]
tests/unit/test_mvp2_auth_consent_profile.py::test_record_measurement_omits_user_id PASSED [ 87%]
tests/unit/test_mvp2_auth_consent_profile.py::test_self_service_consents_endpoints PASSED [100%]

============================== 8 passed in 4.57s ==============================
```

## 3. Mobile TypeScript Typecheck Execution

Command executed:
```bash
npm --prefix mobile run typecheck
```

Command Output:
```
> ai-fashion-assistant-mobile@0.1.0 typecheck
> tsc --noEmit
```
Exit code: 0.
