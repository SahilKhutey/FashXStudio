# Dev Log: Phase 04 Authentication, Shopper Profile and Privacy (Workstream 4.1)

- **Date:** 2026-11-15
- **Branch:** `recovery/rc13.1-governance-correction`
- **Component:** Identity Provider, Cognito Verification Engine, Mobile Auth Client, and Session Revocation

---

## 1. Context & Objectives
Phase 04 establishes the identity and privacy foundation for FashXStudio, transitioning from development mock identities to real, cryptographically verified shopper authentication. Workstream 4.1 specifically targets:
1. Provider selection and architecture consensus.
2. Terraform infrastructure definitions for Amazon Cognito User Pools in `ap-south-1`.
3. Offline RS256 JWKS verification engine supporting Cognito access token claim conventions.
4. Database model and Alembic migration for server-side session revocation tracking.
5. Mobile React Native client structure for PKCE authentication and secure keystore storage.
6. Execution and verification of test cases AUTH-001 through AUTH-018.

---

## 2. Engineering Changes

### 2.1 Provider Decision & ADRs
- Created `docs/adr/0010-identity-provider-cognito.md` and `docs/adr/0006-identity-provider.md` documenting the decision to select Amazon Cognito User Pools in Mumbai (`ap-south-1`).
- Preserved the provider-neutral port (`TokenVerifier` protocol and `SqlIdentityRepo`).

### 2.2 Terraform Infrastructure as Code
- Created `infra/aws/terraform/modules/cognito/`:
  - `main.tf`: Configured `aws_cognito_user_pool` with email verification, password policy, minimal attributes (`email`, `sub`), deletion protection.
  - Public mobile client `aws_cognito_user_pool_client` without client secrets, enforcing OAuth 2.0 PKCE, `code` grant, 15m access token validity, 30d refresh token validity.
  - Domain prefix resource `aws_cognito_user_pool_domain`.
  - Wired into root modules `infra/aws/terraform/environments/{dev, staging, prod}/`.

### 2.3 Database Model & Alembic Migration
- Added `RevokedAuthSession` model to `database/models/auth.py` and exported in `database/models/__init__.py`.
- Created Alembic migration `database/migrations/versions/0034_add_revoked_auth_sessions.py` with unique constraint on `(identity_provider, session_id)` and expiration index.
- Verified single Alembic head with `alembic heads` and test suite `test_migration_state.py`.

### 2.4 Backend Verification Engine & Rate Limiting
- Added Cognito configuration fields and properties to `backend/fashx/core/settings.py`.
- Implemented `backend/fashx/security/cognito.py` with `CognitoTokenVerifier` enforcing:
  - RS256 signature verification via `PyJWKClient` with automatic key rotation.
  - `token_use == "access"` (strictly rejecting ID tokens at API endpoints).
  - `client_id == expected_client_id` (handling Cognito access token claim conventions).
  - Expiry checking with 30s clock skew leeway.
  - Fail-closed behavior on unresolvable keys or provider outages.
- Updated `backend/fashx/security/identity.py` to support `is_session_revoked` and `revoke_session` in both `InMemoryIdentityRepo` and `SqlIdentityRepo`.
- Updated `backend/fashx/security/deps.py` to wire `CognitoTokenVerifier` and check session revocation.
- Added dedicated authentication rate limiters in `backend/fashx/security/ratelimit.py`.

### 2.5 Mobile Client Integration
- Created `mobile/src/auth/`:
  - `authTypes.ts`: Session, tokens, and shopper identity contracts.
  - `secureStorage.ts`: Keystore adapter using `expo-secure-store`.
  - `amplify.ts`: Configuration module for Cognito client and PKCE redirects.
  - `session.ts`: Token caching and retrieval.
  - `authService.ts`: Core sign-up, verification, login, and global sign-out operations.
  - `stores/authStore.ts`: Non-sensitive Zustand UI store (zero tokens stored).
  - `api/authenticatedFetch.ts`: HTTP client wrapper attaching Bearer token.
- Updated `mobile/src/lib/token.ts` to delegate to `getValidAccessToken()`.

---

## 3. Verification & Test Execution
- Auth test suite `tests/security/test_cognito_auth.py`: **18/18 passed in 4.75s**.
- Entire security suite `tests/security/`: **105/105 passed in 38.67s**.
- Migration tests `tests/deployment/test_migration_state.py`: **2/2 passed in 3.12s**.
- Documentation lint: `python scripts/docs_lint.py` passed (`docs lint ok`).
- Code linting: `python -m ruff check` passed clean.
