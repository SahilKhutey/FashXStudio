# RC-01 — Authentication & Identity Architecture

## Overview
FashXStudio implements role-aware and user-scoped authentication across all private API endpoints.

## Authentication Mechanisms

### 1. Development Token Auth
For local development and testing, FastAPI dependency `get_current_user` recognizes development tokens:
- Pattern: `dev-user-...` or configured test user IDs (`demo-user-1`, `test-user-42`).
- Enables rapid testing without requiring external OAuth provider roundtrips during offline or isolated sessions.
- In production (`ENV=prod`), development tokens are rejected, requiring signed JWT bearer tokens validated against public keys.

### 2. Header Contract
Clients pass credentials using standard HTTP Authorization headers:
```http
Authorization: Bearer dev-user-1
```

## Privacy & Consent Controls

### 1. Reference Photo Consent
- Try-on and profile reference photo processing require explicit user consent recorded in `user_consents`.
- Consent types:
  - `reference_photo_storage`: Permission to retain user reference photos.
  - `ai_tryon_processing`: Permission to submit garment and user photo to try-on synthesis models.
- If consent is revoked, try-on job submission immediately rejects with `403 Forbidden` / `CONSENT_REQUIRED`.

### 2. Account Erasure & Data Deletion
- Supported via `DELETE /api/v1/profile/account` or privacy audit deletion endpoints.
- Deletion purges wardrobe records, profile preferences, style quiz picks, and schedules storage object purging for uploaded photos.

## User Isolation Verification
All user-specific repositories (profile, wardrobe, tryon, feed signals) enforce strict scoping by `user_id`:
- Query: `WHERE user_id = :user_id`
- Cross-user access returns `404 Not Found` or `403 Forbidden`, preventing enumeration or privilege escalation.
