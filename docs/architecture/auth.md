# Authentication Architecture & JWKS Configuration

## Overview
FashX uses an identity-agnostic authentication model established in Phase 3. The API never couples authorization logic or entity ownership to third-party provider user IDs. Instead, the backend verifies identity tokens and maps the tuple `(issuer, subject)` to an internal canonical `user_id`.

## Backend Settings (Staging and Production)

To point the backend at Supabase Auth:

```ini
ENV=prod
AUTH_MODE=jwks
AUTH_ISSUER=https://<project-ref>.supabase.co/auth/v1
AUTH_AUDIENCE=authenticated
AUTH_JWKS_URL=https://<project-ref>.supabase.co/auth/v1/.well-known/jwks.json
```

For local hermetic testing:
```ini
ENV=dev
AUTH_MODE=local
AUTH_ISSUER=fashx-test
AUTH_AUDIENCE=fashx-api
AUTH_JWT_SECRET=test-secret-key-at-least-32-chars-long
```

## Security Invariants

1. **Algorithm Pinning:** `JWKSVerifier` accepts only `RS256` and `ES256` asymmetric algorithms, rejecting any `HS256` symmetric confusion attempts.
2. **Claim Validation:** Every token must provide `exp`, `sub`, `iss`, and `aud`. Tokens with an audience other than `authenticated` are rejected with HTTP 401.
3. **Role Decoupling:** Provider-level claims (e.g., Supabase `role: authenticated`) are ignored. Internal roles (`user`, `admin`, etc.) and account statuses are persisted and resolved from `auth_identities`.
4. **Deterministic Identity Resolution:** Multiple concurrent logins from the same user resolve to the single internal `user_id` without race conditions or duplicate account creation.
