# Shopper Profile Alembic Migrations

## 1. Migration Overview
- **Migration ID**: `0036_add_shopper_profiles`
- **Revises**: `0035_add_account_lifecycle_tables`
- **Tables Introduced**:
  - `shopper_profiles`
  - `profile_category_sizes`
  - `profile_measurements`

## 2. DDL Operations
- Primary keys use `UUID` with foreign key references to `users.id` (`ondelete="CASCADE"`).
- Check constraints:
  - `ck_shopper_profiles_height_range`: `height_cm >= 80.0 AND height_cm <= 250.0`
  - `ck_shopper_profiles_weight_range`: `weight_kg >= 20.0 AND weight_kg <= 400.0`
  - `ck_profile_measurements_positive`: `value_cm > 0`
  - `ck_profile_measurements_confidence`: `confidence >= 0 AND confidence <= 1`
- Unique constraints:
  - `uq_shopper_profiles_user_id`: 1:1 relationship with `users.id`
  - `uq_profile_category_sizes_user_cat`: `(user_id, category_code)`

## 3. Rollback Safety
The `downgrade()` function drops tables in reverse dependency order:
1. `profile_measurements`
2. `profile_category_sizes`
3. `shopper_profiles`
