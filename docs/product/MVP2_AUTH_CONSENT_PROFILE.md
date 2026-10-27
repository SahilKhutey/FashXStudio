# MVP 2: Authentication, Consent & User Profiles Verification

## Implementation Overview

MVP 2 binds profile management directly to the authenticated identity, enforces fail-closed identity parsing, introduces append-only versioned consent event auditing, and exposes validated self-service endpoints.

### Key Changes
1. **Authenticated Profile Creation**:
   - `CreateProfileCommand` accepts `user_id: UUID | None`.
   - `CreateProfileUseCase` attaches body profile metrics and consent scopes to the authenticated user ID without generating duplicate or orphaned user records.
   - `POST /api/v1/profile/users` derives `user_id` from the authenticated `Principal`.

2. **Fail-Closed Onboarding Identity**:
   - `principal_user_uuid(principal: Principal)` in `fashx.api.v1.onboarding` replaces the unsafe random-UUID fallback with fail-closed authentication error (`ApiError(401, "unauthorized", ...)`).
   - `POST /api/v1/onboarding/style-quiz/picks` strictly requires valid principal identity.

3. **Append-Only Consent Audit Events**:
   - Model `ConsentEvent` in `database/models/identity.py` tracking `(user_id, data_type, granted, consent_version, policy_url, decision_source, created_at)`.
   - Registered in `database/models/__init__.py`.
   - Alembic migration `0029_consent_events.py` in `database/migrations/versions/`.
   - All consent operations (`upsert`, `record_mobile_consent`, `RevokeConsentUseCase`) record `ConsentEvent` rows atomically alongside `ConsentRecord`.

4. **Self-Service Profile & Consent Endpoints**:
   - `GET /api/v1/profile/me`: Returns derived profile (body metrics, preferences, consents, measurements, photos) for authenticated identity.
   - `PUT /api/v1/profile/preferences`: Supports self-service preference updates with `@model_validator` cross-field check (`budget_min <= budget_max`).
   - `POST /api/v1/profile/measurements`: Automatically binds to authenticated `user_id`; client payload omission of `user_id` supported.
   - `GET /api/v1/profile/consents`: Lists current user consents.
   - `PUT /api/v1/profile/consents/{data_type}`: Updates consent state and logs decision event.

5. **Purpose-Specific Consent Enforced**:
   - Account creation does not require optional body photo uploads.
   - Photo uploads and virtual try-on inference strictly enforce `body_photo` consent.

## Automated Test Verification

Command:
```powershell
pytest tests/unit/test_mvp2_auth_consent_profile.py tests/contracts/test_mobile_contract.py tests/unit/test_profile_use_cases.py -q
```

Output:
```
tests/unit/test_mvp2_auth_consent_profile.py ........                    [ 33%]
tests/contracts/test_mobile_contract.py ............                     [ 83%]
tests/unit/test_profile_use_cases.py ....                                [100%]
24 passed
```
