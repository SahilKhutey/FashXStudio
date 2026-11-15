# FashXStudio User Account Lifecycle

## 1. Objective and Architecture
This document specifies the end-to-end shopper account lifecycle for FashXStudio, spanning account registration, identity provisioning, session management, identity updates, account suspension, and permanent deletion.

### Core Principle: Decoupling Credentials from Application State
- **Identity Provider (Amazon Cognito User Pools)**: Manages authentication credentials, password policies, multi-factor authentication (MFA), and token issuance.
- **Application Backend (FastAPI + PostgreSQL)**: Manages shopper profile attributes, consent records, uploaded photos, wardrobe items, virtual try-on history, and session revocation registries.

## 2. Lifecycle Operations (Tasks 4.2.1 – 4.2.12)

### 4.2.1 Account Registration & Idempotent Provisioning
- **Mobile Flow**: Shopper registers via Cognito SDK (`signUp`).
- **Backend Flow (`POST /api/v1/account/provision`)**:
  - Validates caller principal (verified Cognito JWT with `sub`).
  - Idempotently creates or resolves internal `User` and `IdentityAccount` records.
  - Normalizes email to lowercase standard.
  - Returns internal `user_id` and initial `account_status`.

### 4.2.2 Account Verification
- Shopper submits email verification code to Cognito (`confirmSignUp`).
- Upon successful confirmation, Cognito issues verified tokens (`email_verified: true`).
- Backend reconciliation endpoint marks `email_verified = true` and updates user state to `ACTIVE`.

### 4.2.3 Login & Session Resolution (`GET /api/v1/account/me`)
- Returns authenticated shopper details:
  - `user_id`: Canonical internal UUID
  - `email_normalized`: Cleaned lowercase email
  - `email_verified`: Verification flag
  - `account_status`: Lifecycle status (`ACTIVE`, `DISABLED`, etc.)
  - `roles`: Role set (e.g. `["user"]`)
  - `created_at`: Account timestamp

### 4.2.4 Session Refresh
- Handled transparently by client-side SDK via Cognito token endpoint using refresh tokens.
- Secure token storage using Expo `SecureStore` (iOS Keychain / Android Keystore). Never stored in unencrypted `AsyncStorage` or client state trees.

### 4.2.5 Logout & Session Revocation (`POST /api/v1/account/sessions/revoke-all`)
- Invalidates all active refresh and access tokens.
- Records global revocation timestamp in `revoked_auth_sessions` and sets session status in `auth_sessions`.
- Subsequent API requests using issued JWTs fail closed with HTTP 401 Unauthorized.

### 4.2.6 Account Recovery (Password Reset)
- Shopper initiates password reset via Cognito (`forgotPassword`).
- All backend-facing recovery endpoints return uniform, non-enumerating responses (HTTP 200/202) regardless of whether the email address exists in the system.

### 4.2.7 Email Change Workflow
- Shopper requests email change (`POST /api/v1/account/email-change`).
- Verification challenge sent to new email address.
- Shopper confirms challenge code (`POST /api/v1/account/email-change/confirm`).
- Updates `email_normalized` with strict PostgreSQL unique constraint validation.

### 4.2.8 Account Disabling (`POST /api/v1/account/disable`)
- Shopper or authorized administrator disables the account.
- Sets account state to `DISABLED`, records `disabled_at`.
- Revokes all active sessions. Future requests return HTTP 403 Forbidden ("Account is disabled").

### 4.2.9 Permanent Account Deletion Workflow
- Shopper requests deletion (`POST /api/v1/account/deletion-request`).
- Sets account state to `DELETION_PENDING`, revokes active sessions.
- Enqueues durable async deletion job in `account_deletion_jobs`.
- Durable worker executes complete cleanup:
  1. Purges private S3 objects (`users/{user_id}/` and `tryon/{user_id}/`).
  2. Erases personal database records (biometrics, wardrobe, profile, preferences).
  3. Writes immutable tombstone to `erasure_tombstones`.
  4. Deletes external Cognito identity or revokes IdP profile.
  5. Updates job to `COMPLETED` and account status to `DELETED`.

### 4.2.10 Duplicate Registration & Concurrency Protection
- Enforced at PostgreSQL schema level:
  - `UNIQUE (email_normalized)` on `users` table.
  - `UNIQUE (provider, provider_subject)` on `identity_accounts` table.
- Concurrent registration requests safely handle race conditions via database transactions and idempotent upserts.

### 4.2.11 Account Enumeration Defenses
- Public auth endpoints (registration, forgot password, email verification) provide identical timing profiles and generic responses to prevent user existence probing.
- Distributed Redis rate limiter applies per-IP and per-email sliding window limits.

### 4.2.12 Concurrent Sessions Management
- Session registry table `auth_sessions` tracks active sessions by `user_id`, `provider`, and token `jti`.
- Allows shoppers to view active devices and revoke individual or all sessions remotely.
