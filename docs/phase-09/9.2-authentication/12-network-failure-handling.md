# 12 — Network Failure Handling

## Error Normalization (`mobile/src/auth/auth.errors.ts`)
- `AuthError` codes: `NETWORK_UNAVAILABLE`, `REQUEST_TIMEOUT`, `AUTHENTICATION_FAILED`, `ACCOUNT_UNVERIFIED`, `VERIFICATION_CODE_INVALID`, `VERIFICATION_CODE_EXPIRED`, `PASSWORD_POLICY_VIOLATION`, `RATE_LIMITED`, `AUTH_SERVICE_UNAVAILABLE`, `SESSION_EXPIRED`, `UNKNOWN_ERROR`.
- `toAuthUserMessage(error)` returns safe user-facing copy without exposing stack traces, hostnames, or provider internals.
- `RegisterScreen`, `LoginScreen`, `VerificationScreen`, and `RecoveryScreen` disable duplicate submissions while loading and preserve email inputs on transient network failures.
