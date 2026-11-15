# ADR-0010: Identity Provider — Amazon Cognito User Pools

- **Status:** Accepted (supersedes ADR-0007; also tracked as ADR-0006)
- **Date:** 2026-11-15
- **Owner:** Sahil Khutey

---

## 1. Context

FashXStudio is deployed on AWS Mumbai (`ap-south-1`) with ECS Fargate, RDS PostgreSQL 16, Amazon ElastiCache (Valkey/Redis 7.2), Amazon S3 private storage, and AWS Secrets Manager.

Authentication establishes the identity and security boundary for all sensitive shopper data:
- Profile photos and biometric measurements (height, weight, body shape, skin tone).
- Virtual try-on (VTO) source photos and generation results.
- Style preferences, wardrobe collections, and saved items.
- Statutory consent records under applicable data privacy frameworks.

In October 2026, ADR-0007 proposed Supabase Auth for an invite-only pilot. A comprehensive repository and infrastructure audit conducted in November 2026 revealed:
1. Supabase was never operational in production or staging. Only placeholder configuration existed (`dummy-fashx.supabase.co`).
2. There are zero live shopper accounts, zero migrations, and zero database tables bound to Supabase.
3. The backend architecture already employs a provider-neutral port (`TokenVerifier` protocol and `auth_identities` table mapping `(issuer, subject)` to internal `User` UUIDs).
4. Running Supabase alongside AWS would introduce an external identity control plane, redundant egress, separate billing, and conflicting compliance regimes.

---

## 2. Decision

Adopt **Amazon Cognito User Pools** in `ap-south-1` (Mumbai) as FashXStudio's primary shopper identity provider:

1. **Environment Isolation**: Independent user pools per deployment tier:
   - Development: `fashx-dev-users`
   - Staging: `fashx-staging-users`
   - Production: `fashx-prod-users`
2. **Minimal Attribute Footprint**:
   - Cognito stores **only** authentication credentials: `email` (login identifier and verification target), `email_verified`, and immutable `sub`.
   - **Zero** body measurements, skin-tone preferences, photos, or biometric attributes are stored in Cognito attributes. All shopper profile data resides in FashXStudio's PostgreSQL database with explicit consent gates.
3. **Public Mobile App Client**:
   - Public client type without client secrets (`generate_secret = false`).
   - OAuth 2.0 Authorization Code Grant with mandatory **PKCE (Proof Key for Code Exchange)**.
   - Allowed scopes restricted to `openid` and `email`.
   - Callback schemes: `fashx://auth/callback` (production) and `fashx-staging://auth/callback` (staging).
4. **Token Strategy**:
   - Access token lifetime: 15 minutes (used for FastAPI API requests).
   - ID token lifetime: 15 minutes (client-side identity display only; strictly rejected at API endpoints).
   - Refresh token lifetime: 30 days.
   - Signing algorithm: Asymmetric **RS256** with automatic JWKS public-key caching and rotation.
5. **Backend Verification Engine (`CognitoTokenVerifier`)**:
   - FastAPI validates access tokens locally using cached public keys from Cognito's JWKS endpoint (`https://cognito-idp.ap-south-1.amazonaws.com/<userPoolId>/.well-known/jwks.json`).
   - Verifies signature, `iss == expected_issuer`, `client_id == expected_app_client_id`, `token_use == "access"`, and `exp > now`.
   - Rejects ID tokens (`token_use == "id"`), symmetric HMAC tokens, and malformed algorithms.
6. **Local Revocation & Global Sign-Out**:
   - Offline JWT verification cannot observe Cognito server-side revocation in real time. FashXStudio implements a database-backed `revoked_auth_sessions` table tracking revoked `session_id` (`origin_jti` / `jti`) until token expiry.
   - Protected API calls verify session validity against the revocation table before granting access.
7. **Identity Resolution**:
   - Stable Cognito `sub` resolves to an internal FashXStudio `User` UUID via `auth_identities`. The mobile client never supplies or dictates internal user IDs.

---

## 3. Comparison of Alternatives

| Evaluation Dimension | Amazon Cognito User Pools (Selected) | Supabase Auth (Superseded ADR-0007) | Clerk |
|---|---|---|---|
| **Cloud Alignment** | Native AWS Mumbai (`ap-south-1`), IAM, CloudWatch, Terraform | Separate platform, redundant egress | Separate third-party SaaS |
| **Operational State** | Greenfield provision via existing Terraform IaC | Never provisioned; only placeholder dummy URLs | Not evaluated beyond SaaS audit |
| **JWT Verification** | RS256 JWKS public key rotation, `token_use="access"`, `client_id` | RS256 JWKS with `aud="authenticated"` | RS256 JWKS |
| **Mobile Integration** | AWS Amplify Auth / Expo AuthSession + PKCE | Pure JS SDK | React Native Expo SDK |
| **Cost & Quotas** | 50,000 free MAU on AWS free tier, billed within AWS account | Separate tier, project pause risks | Per-MAU pricing tier |
| **Migration Risk** | Zero (no existing accounts or live databases) | N/A | High vendor lock-in |

---

## 4. Security & Privacy Guarantees

1. **No Client Secrets in Mobile Binaries**: Mobile applications are public clients; PKCE protects code exchange without embedded secrets.
2. **Zero Credentials in Application Logs**: Passwords, authorization codes, refresh tokens, and raw JWT headers are scrubbed by the observability redaction filter.
3. **Fail-Closed Verification**: If Cognito JWKS is unreachable or signing keys cannot be retrieved, token verification fails with HTTP 401.
4. **Consent Decoupling**: Authenticating with Cognito grants identity verification only; Virtual Try-On photo uploads require independent, versioned consent in PostgreSQL.
