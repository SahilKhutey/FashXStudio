# Phase 04.3 — Shopper Profile Architecture

## 1. Overview and Boundary Scope
The Shopper Profile subsystem manages structured sizing, fit, style, and shopping preferences for shoppers in FashXStudio.

### Explicit Boundary Isolation
- **Included in Scope (Phase 04.3)**:
  - Structured physical attributes: `height_cm` and optional `weight_kg` in metric units.
  - Sizing preferences: `preferred_size_system` (IN, US, UK, EU, INTL) and category-level sizing overrides (`profile_category_sizes`).
  - Fit preferences: `preferred_fit` (SLIM, REGULAR, RELAXED, OVERSIZED, NO_PREFERENCE).
  - Style & aesthetic preferences: controlled taxonomy of styles, color palettes, and preferred product categories.
  - Shopping preferences: budget ranges, occasions/intents, preferred brands, avoided materials, and sustainability preference.
  - Unit normalization utilities (Decimal precision for inches, feet, pounds).
  - Optimistic concurrency control via incremented `version` column.
  - Dynamic feature completeness calculation.
  - Mobile client integration (React Native, TypeScript, Zustand).

- **Excluded from Scope (Deferred to Phases 04.4–04.6)**:
  - User body photos, try-on image uploads, and biometric inferences.
  - Automated 3D body scanning, computer vision pose estimation, and virtual try-on pipelines.
  - Consent capture records and marketing preferences (governed by DPDP/GDPR consent modules).

## 2. High-Level Data Flow

```
+--------------------------------------------------------------------+
|               Mobile Client (React Native / Expo)                  |
|  - ProfileScreen                                                   |
|  - EditPhysicalProfileScreen / EditStylePreferencesScreen          |
|  - Zustand store (useProfileStore) with session-clearing on logout |
+---------------------------------+----------------------------------+
                                  |
                                  | HTTPS + Bearer JWT
                                  v
+--------------------------------------------------------------------+
|                 FastAPI Application Tier (/profile)                |
|  - Principal Dependency: JWT extraction (user_id from token sub)   |
|  - Account Status Gate: Active check (blocks disabled/deleting)    |
|  - Schema Validation: Pydantic v2 (extra="forbid")                 |
|  - Unit Normalization: Exact Decimal conversion                    |
+---------------------------------+----------------------------------+
                                  |
                                  v
+--------------------------------------------------------------------+
|               Profile Domain Service & Repository                  |
|  - ShopperProfileService: Business rules, completeness calculation |
|  - ShopperProfileRepository: Optimistic locking, transactional CRUD|
+---------------------------------+----------------------------------+
                                  |
                                  v
+--------------------------------------------------------------------+
|                     PostgreSQL Database Engine                     |
|  - shopper_profiles (1:1 with users.id)                            |
|  - profile_category_sizes (1:N category size overrides)            |
|  - profile_measurements (1:N audit/history records)                |
+--------------------------------------------------------------------+
```

## 3. Core Architecture Tenets

1. **Zero-Trust Identity Derivation**:
   - The API endpoint `/api/v1/profile/me` derives the shopper identity strictly from the verified JWT `Principal.user_id`.
   - Client requests cannot pass arbitrary `user_id` values to inspect or update another user's profile.

2. **Mass-Assignment Defense**:
   - Pydantic models enforce `extra="forbid"`. Client payloads providing `id`, `user_id`, `version`, `created_at`, or `updated_at` are rejected with HTTP 422 Unprocessable Entity.

3. **Optimistic Concurrency Control**:
   - Each profile row maintains an integer `version` field.
   - When clients supply `expected_version` on update, a mismatch triggers HTTP 409 Conflict without writing stale data.

4. **Non-Medical Physical Profile**:
   - Height and weight attributes are strictly stored as ergonomic metric dimensions (height 80–250 cm, weight 20–400 kg).
   - No BMI scores, body fat percentages, or clinical health markers are calculated or persisted.
