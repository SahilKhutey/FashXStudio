# 15 — Phase 09.2 Test Plan

## Local Automated Coverage
- `mobile/__tests__/phase09_2_auth.test.tsx`:
  - `maskEmail` destination masking & `toAuthUserMessage` internal error redaction
  - `ProviderAuthService` delegation
  - `refreshSessionOnce` single-flight concurrency coalescing
  - `initializeAuthSession` session restoration
  - `performAppLogout` offline-safe cleanup of `purgeLocalSession`, `queryClient`, and `useAppStore`
  - `RegisterScreen`, `LoginScreen`, `VerificationScreen`, and `RecoveryScreen` validation & provider callbacks
- Existing suites: `auth_and_api.test.ts`, `dev_token_gate.test.ts`, `client.test.ts`, `route-policy.test.ts`, `settings_and_privacy.test.ts`.

## Pending Live / Device Coverage
- Live identity-provider registration, verification, recovery, and refresh against staging.
- Physical Android and iOS device lifecycle tests (`DEV-001`–`DEV-015`).
