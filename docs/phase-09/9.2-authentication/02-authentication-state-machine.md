# 02 — Authentication State Machine

## States (`mobile/src/auth/auth.types.ts`)
`INITIALIZING` | `UNAUTHENTICATED` | `REGISTERING` | `VERIFICATION_REQUIRED` | `AUTHENTICATING` | `AUTHENTICATED` | `REFRESHING` | `RECOVERY_PENDING` | `RESETTING_PASSWORD` | `NETWORK_ERROR` | `SESSION_EXPIRED` | `LOGGING_OUT`.

## Guarantees
- UI auth store (`mobile/src/auth/stores/authStore.ts`) holds only non-sensitive UI flags (`isAuthenticated`, `isLoading`, `userId`, `authError`) and zero raw tokens.
- Protected routes remain gated by `mobile/src/navigation/route-policy.ts` and `mobile/app/_layout.tsx` until session initialization completes.
