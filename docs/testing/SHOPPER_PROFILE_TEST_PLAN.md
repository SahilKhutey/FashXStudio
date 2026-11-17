# Shopper Profile Test Plan

## 1. Scope
Validation and regression testing for Phase 04.3 — Shopper Profile.

## 2. Test Matrix

| Test Suite | Test Function | Purpose / Assertion |
| :--- | :--- | :--- |
| `test_unit_normalization.py` | `test_inches_to_cm_standard_values` | Exact Decimal conversion of inches to cm. |
| `test_unit_normalization.py` | `test_feet_inches_to_cm_standard_values` | Exact conversion of ft/in to cm. |
| `test_unit_normalization.py` | `test_pounds_to_kg_standard_values` | Exact conversion of lbs to kg. |
| `test_unit_normalization.py` | `test_unit_conversion_invalid_inputs` | Rejection of negative / out-of-range inputs. |
| `test_shopper_profile_validation.py` | `test_height_range_validation` | Range boundaries 80.0 to 250.0 cm. |
| `test_shopper_profile_validation.py` | `test_weight_range_validation` | Range boundaries 20.0 to 400.0 kg. |
| `test_shopper_profile_validation.py` | `test_physical_attributes_optional` | Verifies profile creation without physical data. |
| `test_shopper_profile_validation.py` | `test_controlled_enums_validation` | Enforces controlled vocabulary for sizes/fit. |
| `test_shopper_profile_validation.py` | `test_style_and_color_preferences_validation` | Validates style, color, category enums. |
| `test_shopper_profile_validation.py` | `test_shopping_preferences_budget_validation` | Validates budget.min <= budget.max and >= 0. |
| `test_shopper_profile_validation.py` | `test_mass_assignment_protection` | Rejects extra fields (user_id, version, etc.). |
| `test_shopper_profile_ownership.py` | `test_shopper_profile_ownership_isolation` | Verifies isolation between User A and User B. |
| `test_shopper_profile_ownership.py` | `test_disabled_account_blocked` | 403 Forbidden on disabled user accounts. |
| `test_shopper_profile_ownership.py` | `test_deletion_pending_account_blocked` | 403 Forbidden on deletion-pending accounts. |
| `test_shopper_profile_ownership.py` | `test_unauthenticated_request_rejected` | 401 Unauthorized when token is missing/invalid. |
| `test_shopper_profile_api.py` | `test_get_profile_me_auto_creates_default` | Auto-initialization of empty profile. |
| `test_shopper_profile_api.py` | `test_put_profile_me_create_or_replace` | Full profile create/replace via PUT. |
| `test_shopper_profile_api.py` | `test_patch_profile_me_partial_update` | Partial update preserving omitted fields. |
| `test_shopper_profile_api.py` | `test_patch_profile_me_clearing_fields` | Explicit clearing of optional fields via null. |
| `test_shopper_profile_api.py` | `test_optimistic_locking_conflict` | 409 Conflict on version mismatch. |
| `test_shopper_profile_api.py` | `test_feature_completeness_endpoint` | Verifies feature readiness flags and percentage. |
| `test_shopper_profile_api.py` | `test_category_sizes_endpoints` | GET and PUT for category-specific sizing. |
