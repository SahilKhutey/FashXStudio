# 14 — Database Migrations

- **Revision**: `0057_add_shopper_fit_profile_and_history`
- **Revises**: `0056_add_product_size_data_and_revisions`
- **File**: `database/migrations/versions/0057_add_shopper_fit_profile_and_history.py`

## Schema Changes

1. `shopper_profiles`: Adds `preferred_measurement_unit` (`String(8)`, default `"CM"`).
2. `profile_measurements`: Adds `measurement_subject` (`BODY`), `original_value`, `original_unit`, `normalized_value`, `normalized_unit`, `measurement_method`, `status`, `validation_status`, `policy_version`, `schema_version`, `measured_at`, `created_at`, `updated_at`, `verified_at`, `expires_at`, `version`, check constraint `ck_profile_measurements_version`, and unique constraint `uq_profile_measurements_user_type`.
3. `profile_measurement_history`: Immutable change history (`user_id` FK `users.id` ON DELETE CASCADE).
4. `category_fit_preferences`: Subjective category preferences (`user_id` FK `users.id` ON DELETE CASCADE, unique `(user_id, category)`).
5. `profile_audit_events`: Sanitized event log (`user_id`, `event_type`, `actor_id`, `details_json`, `created_at`).
