# FashXStudio — Phase 04 Authentication & Identity Architecture

- **Status:** Implemented (Verification Gate: 🟢 Code and CI Pass)
- **Target Platform:** AWS Mumbai (`ap-south-1`)
- **Identity Provider:** Amazon Cognito User Pools
- **Mobile Stack:** React Native (Expo) + AWS Amplify Auth
- **Backend:** FastAPI + PyJWT (RS256 JWKS offline verification) + SQLAlchemy AsyncSession

---

## 1. Executive Summary & Identity Boundary

Authentication in FashXStudio establishes the foundational identity boundary for all sensitive shopper data:
- Profile photos and biometric measurements (height, weight, body shape, skin tone).
- Virtual try-on (VTO) inputs and synthesized results.
- Wardrobe collections, style preferences, and merchant interactions.
- Regulatory consent records under DPDP / GDPR frameworks.

```
+-----------------------------------------------------------------------------------------+
|                                    IDENTITY LIFECYCLE                                    |
|                                                                                         |
|   Shopper               Amazon Cognito                   FastAPI Backend     PostgreSQL |
|   (Mobile App)          (ap-south-1 Mumbai)             (ECS Fargate)       (RDS Pg16)  |
|        |                         |                             |                 |      |
|        | 1. Sign Up / Sign In    |                             |                 |      |
|        |------------------------>|                             |                 |      |
|        | 2. Auth Code + PKCE     |                             |                 |      |
|        |<------------------------|                             |                 |      |
|        | 3. Access/ID/Refresh    |                             |                 |      |
|        |<------------------------|                             |                 |      |
|        |                         |                             |                 |      |
|        | 4. API Request + Bearer Access Token                  |                 |      |
|        |------------------------------------------------------>|                 |      |
|        |                         |                             |                 |      |
|        |                         | 5. Offline JWKS Verify      |                 |      |
|        |                         |    - RS256 Public Key       |                 |      |
|        |                         |    - token_use == 'access'  |                 |      |
|        |                         |    - client_id == expected  |                 |      |
|        |                         |    - iss == user_pool_url   |                 |      |
|        |                         |                             |                 |      |
|        |                         |                             | 6. Check Revoke |      |
|        |                         |                             |---------------->|      |
|        |                         |                             | 7. Map sub->UUID|      |
|        |                         |                             |---------------->|      |
|        | 8. Protected API Response (200 OK)                    |                 |      |
|        |<------------------------------------------------------|                 |      |
+-----------------------------------------------------------------------------------------+
```

---

## 2. Core Architectural Decisions

### 2.1 Provider Selection & Audit Outcome
A comprehensive audit of the codebase confirmed that Supabase Auth was never operational in production or staging; it existed only as configuration stubs (`dummy-fashx.supabase.co`). Selecting **Amazon Cognito User Pools** in `ap-south-1` (Mumbai) achieves 100% infrastructure consistency with FashXStudio's ECS Fargate, RDS PostgreSQL 16, Amazon ElastiCache, S3, Secrets Manager, and CloudWatch stack, incurring zero migration risk.

### 2.2 Minimal Attribute Footprint
Cognito stores **only** authentication credentials:
- `sub`: Immutable unique identity reference.
- `email`: Primary sign-in identifier and delivery channel for 6-digit verification codes.
- `email_verified`: Cryptographically confirmed state.

**Strict Privacy Rule:** Zero body measurements, skin-tone preferences, photos, or biometric attributes are stored in Cognito attributes. All shopper profile data resides in FashXStudio's PostgreSQL database with explicit consent gates.

### 2.3 Mobile Public Client & PKCE
- Client Type: Public mobile client without client secrets (`generate_secret = false`).
- OAuth Flow: Authorization Code Grant with mandatory **PKCE (Proof Key for Code Exchange)**.
- Scopes: Restricted to `openid` and `email`.
- Custom URI Schemes:
  - Development: `fashx-dev://auth/callback` & `fashx-dev://auth/logout`
  - Staging: `fashx-staging://auth/callback` & `fashx-staging://auth/logout`
  - Production: `fashx://auth/callback` & `fashx://auth/logout`

### 2.4 Token Durations & Types
| Token | Lifetime | Allowed Usage | Enforcement |
|---|---|---|---|
| **Access Token** | 15 minutes | FastAPI Bearer authentication | Verified via `client_id`, `token_use == "access"` |
| **ID Token** | 15 minutes | Client-side UI profile claims | **Strictly rejected** at API endpoints (`token_use != "access"`) |
| **Refresh Token** | 30 days | Native mobile session renewal | Managed via AWS Amplify / Keystore; never sent to API |

---

## 3. Backend Verification Engine (`CognitoTokenVerifier`)

The backend implements offline verification (`backend/fashx/security/cognito.py`) using `PyJWKClient`:
1. **Public Key Caching & Rotation**: Caches public keys with a 1-hour TTL. If a token presents an unknown `kid`, the client re-fetches the JWKS keyset automatically.
2. **Algorithm Lockdown**: Restricts signatures strictly to `RS256`. Symmetrically signed tokens (`HS256`) and unsecured tokens (`alg: none`) are rejected with HTTP 401.
3. **Cognito Claim Conventions**: Cognito access tokens contain `client_id` (not `aud`), `token_use == "access"`, and `scope`. The verifier specifically checks `client_id == settings.cognito_app_client_id` rather than ID-token audience checks.
4. **Session Identifier Tracking**: Extracts `origin_jti` (or `jti`) to track the persistent root session for logout and revocation checks.

---

## 4. Session Revocation & Global Sign-Out

Offline JWT verification cannot observe Cognito server-side revocation in real time. FashXStudio bridges this gap using a database-backed revocation table:

```sql
CREATE TABLE revoked_auth_sessions (
    id UUID PRIMARY KEY,
    identity_provider VARCHAR(32) NOT NULL,
    subject VARCHAR(255) NOT NULL,
    session_id VARCHAR(255) NOT NULL,
    revoked_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT uq_revoked_auth_sessions_provider_session UNIQUE (identity_provider, session_id)
);
CREATE INDEX ix_revoked_auth_sessions_expires_at ON revoked_auth_sessions (expires_at);
```

When a user signs out globally:
1. The client invokes Cognito global sign-out.
2. The session revocation endpoint logs the `session_id` (`origin_jti`) into `revoked_auth_sessions`.
3. Every protected API request verifies `repo.is_session_revoked(provider, session_id)`. Revoked sessions immediately return HTTP 401.

---

## 5. Rate Limiting & Abuse Prevention

Dedicated rate limits are enforced at the API layer (`backend/fashx/security/ratelimit.py`):
- **Login Attempts**: 5 attempts per 15 minutes per IP/account (`rate_limit_auth_login`).
- **Verification Code Resend**: 3 requests per 15 minutes (`rate_limit_auth_verification`).
- **Password Reset Requests**: 3 requests per 15 minutes (`rate_limit_password_reset`).

Generic error responses are returned across all authentication endpoints to prevent user account enumeration.

---

## 6. Verification Test Matrix (AUTH-001 - AUTH-018)

| Test ID | Scenario | Expected Result | Automated Status |
|---|---|---|---|
| **AUTH-001** | Valid access token with RS256 signature, correct client ID and issuer | Accepted (Principal resolved) | 🟢 PASSED |
| **AUTH-002** | Missing Authorization header | HTTP 401 Unauthorized | 🟢 PASSED |
| **AUTH-003** | Malformed JWT string | HTTP 401 Unauthorized | 🟢 PASSED |
| **AUTH-004** | Invalid signature (foreign key) | HTTP 401 Unauthorized | 🟢 PASSED |
| **AUTH-005** | Expired access token (`exp < now`) | HTTP 401 Unauthorized | 🟢 PASSED |
| **AUTH-006** | Wrong issuer (`iss` mismatch) | HTTP 401 Unauthorized | 🟢 PASSED |
| **AUTH-007** | Wrong app client ID (`client_id` mismatch) | HTTP 401 Unauthorized | 🟢 PASSED |
| **AUTH-008** | ID token presented at API (`token_use == "id"`) | HTTP 401 Unauthorized | 🟢 PASSED |
| **AUTH-009** | Unsupported algorithm (`alg: none` or `HS256`) | HTTP 401 Unauthorized | 🟢 PASSED |
| **AUTH-010** | Unknown signing key with unresolved JWKS | HTTP 401 (Fail-Closed) | 🟢 PASSED |
| **AUTH-011** | Revoked session (`session_id` in `revoked_auth_sessions`) | HTTP 401 Unauthorized | 🟢 PASSED |
| **AUTH-012** | Scope extraction verification | Correct scope set extracted | 🟢 PASSED |
| **AUTH-013** | Empty subject claim | HTTP 401 Unauthorized | 🟢 PASSED |
| **AUTH-014** | JWKS provider unavailable / network timeout | HTTP 401 (Fail-Closed) | 🟢 PASSED |
| **AUTH-015** | Distinct token subjects | Principals isolated to respective users | 🟢 PASSED |
| **AUTH-016** | Local session revocation blocks subsequent request | First call 200, second call 401 | 🟢 PASSED |
| **AUTH-017** | Concurrent logins for same Cognito subject | Single deterministic user UUID | 🟢 PASSED |
| **AUTH-018** | Authentication rate limiting threshold | 5 allowed, 6th returns HTTP 429 | 🟢 PASSED |
