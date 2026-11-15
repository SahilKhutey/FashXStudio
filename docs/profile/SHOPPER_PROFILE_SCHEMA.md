# Shopper Profile Database Schema

## 1. Relational Design
The Shopper Profile subsystem comprises three primary tables in PostgreSQL, established via Alembic migration `0036_add_shopper_profiles`.

```
                +-------------------+
                |       users       |
                | (id: UUID, PK)    |
                +---------+---------+
                          |
              1:1 Unique  |  1:N
        +-----------------+-----------------+
        |                                   |
        v                                   v
+-----------------------+       +------------------------+
|   shopper_profiles    |       | profile_category_sizes |
| (id: UUID, PK)        |       | (id: UUID, PK)         |
| (user_id: UUID, FK, U)|       | (user_id: UUID, FK)    |
| (version: INT, >= 1)  |       | (category_code: TEXT)  |
| (height_cm: NUMERIC)  |       | (size_system: TEXT)    |
| (weight_kg: NUMERIC)  |       | (size_label: TEXT)     |
| (preferred_fit: TEXT) |       +------------------------+
| (style_prefs: JSONB)  |                   |
| (shopping_prefs:JSONB)|                   | 1:N
+-----------------------+                   v
                                +------------------------+
                                |  profile_measurements  |
                                | (id: UUID, PK)         |
                                | (user_id: UUID, FK)    |
                                | (measurement_type:TEXT)|
                                | (value_cm: NUMERIC)    |
                                +------------------------+
```

## 2. Table Specifications

### 2.1 `shopper_profiles`
- `id`: UUID (Primary Key, default uuid4).
- `user_id`: UUID (Foreign Key to `users.id` ON DELETE CASCADE, Unique constraint).
- `height_cm`: NUMERIC(5, 1) NULL. Check constraint: `height_cm >= 80.0 AND height_cm <= 250.0`.
- `weight_kg`: NUMERIC(5, 1) NULL. Check constraint: `weight_kg >= 20.0 AND weight_kg <= 400.0`.
- `preferred_size_system`: VARCHAR(16) NULL (IN, US, UK, EU, INTL).
- `preferred_fit`: VARCHAR(32) NULL (SLIM, REGULAR, RELAXED, OVERSIZED, NO_PREFERENCE).
- `style_preferences`: JSONB NOT NULL DEFAULT '[]'::jsonb.
- `preferred_colors`: JSONB NOT NULL DEFAULT '[]'::jsonb.
- `product_categories`: JSONB NOT NULL DEFAULT '[]'::jsonb.
- `shopping_preferences`: JSONB NOT NULL DEFAULT '{}'::jsonb.
- `version`: INTEGER NOT NULL DEFAULT 1.
- `created_at`: TIMESTAMPTZ NOT NULL DEFAULT now().
- `updated_at`: TIMESTAMPTZ NOT NULL DEFAULT now().

### 2.2 `profile_category_sizes`
- `id`: UUID (Primary Key).
- `user_id`: UUID (Foreign Key to `users.id` ON DELETE CASCADE, Indexed).
- `category_code`: VARCHAR(64) NOT NULL.
- `size_system`: VARCHAR(16) NOT NULL.
- `size_label`: VARCHAR(32) NOT NULL.
- `updated_at`: TIMESTAMPTZ NOT NULL DEFAULT now().
- Unique Index: `(user_id, category_code)`.

### 2.3 `profile_measurements`
- `id`: UUID (Primary Key).
- `user_id`: UUID (Foreign Key to `users.id` ON DELETE CASCADE, Indexed).
- `measurement_type`: VARCHAR(64) NOT NULL.
- `value_cm`: NUMERIC(5, 1) NOT NULL. Check constraint: `value_cm > 0`.
- `confidence`: NUMERIC(4, 3) NULL. Check constraint: `confidence >= 0 AND confidence <= 1`.
- `source`: VARCHAR(32) NOT NULL DEFAULT 'USER_ENTERED'.
- `created_at`: TIMESTAMPTZ NOT NULL DEFAULT now().

## 3. Data Deletion & Privacy Compliance
All profile tables reference `users.id` with `ON DELETE CASCADE`. In addition, `shopper_profiles`, `profile_category_sizes`, and `profile_measurements` are registered within `backend/fashx/application/erasure.py` (`ACCOUNT_TABLES`) ensuring automated erasure when an account deletion workflow executes.
