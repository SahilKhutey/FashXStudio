# ADR-0002: Canonical User and Profile Model

## Status
Accepted

## Context
Across initial scaffolding and feature specifications, three overlapping user/profile representations existed:
1. **Core Foundation Profile:** `User`, `BodyProfile`, `UserMeasurement`, `UserPreference`, `UserPhoto`, `ConsentRecord` (defined in `database/models/identity.py` and `database/models/profile.py`).
2. **F02 Onboarding Profile:** `OnboardingProfile` (defined in `database/models/profile.py`, migration `0013_onboarding_profiles`).
3. **C13 Customer Models:** `Customer`, `CustomerPreferences`, `CustomerAddress`, `CustomerConsent` (defined in `backend/fashx/repositories/customer/memory.py`).

Persisting multiple divergent models for identity, preferences, and body metrics would create schema collisions, duplicate data pipelines, and unreliable foreign key cascading upon right-to-erasure invocation.

## Decision
1. **Canonical Identity Root:**
   - `users.id` (UUID) is the canonical primary key for every user.
   - Linked to `auth_identities(issuer, subject, user_id)` (Phase 3). Every authenticated request resolves `(issuer, subject) -> users.id`.
   - All user-owned tables across MVP domains strictly reference `users.id` with `ON DELETE CASCADE`.

2. **Canonical Profile Subsystem:**
   - The Foundation Profile models (`BodyProfile`, `UserMeasurement`, `UserPreference`, `UserPhoto`, `ConsentRecord`) represent the single source of truth for body measurements, visual styling, try-on calibrations, and discovery feed scoring.
   - Empirical evidence shows all MVP use cases (`backend/fashx/profile/`, `backend/fashx/tryon/`, `backend/fashx/recommendation/`, `backend/fashx/commerce_wardrobe/`) read and write these exact models through `ProfileUnitOfWork`.

3. **Onboarding Context Integration:**
   - `OnboardingProfile` (`onboarding_profiles`) is retained as an auxiliary onboarding lifecycle state machine referencing `users.id` via foreign key. It does not replace or duplicate body measurements or preferences.

4. **C13 Customer Separation:**
   - Legacy `CustomerAddress` and delivery preferences remain isolated within frozen commerce domains (`backend/fashx/domain/customer/` and `backend/fashx/repositories/customer/`). They are unmounted in production runtime and do not interact with MVP persistence.

5. **Consent & Erasure Governance:**
   - Consent records reside strictly in `consent_records(user_id, data_type, granted)`.
   - Revocation cascades cleanly:
     - Biometric revoke purges `user_photos`, `user_measurements`, `body_profiles`, and `tryon_jobs`.
     - Account deletion cascades across `users.id` to remove all preferences, wardrobe items, feedback, and auth credentials, while anonymizing append-only analytics events.

## Consequences
- Guaranteed referential integrity and single source of truth.
- Elimination of duplicate preference models in MVP routes.
- Fully auditable cascading erasure satisfying DPDP and GDPR requirements.
