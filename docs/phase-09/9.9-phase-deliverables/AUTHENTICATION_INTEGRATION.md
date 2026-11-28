# Authentication Integration

- **Abstraction**: `ProviderAuthService` (`mobile/src/auth/auth.service.ts`) delegates to `AuthProvider` (`supabase.provider.ts`), separating UI screens from identity-provider SDK details.
- **Flows Implemented**:
  - Registration (`register`) returning `AUTHENTICATED` or `VERIFICATION_REQUIRED`
  - Account verification (`confirmRegistration`, `resendVerificationCode`)
  - Login (`login`)
  - Password recovery (`startRecovery`, `completeRecovery`)
  - Session inspection & refresh (`getCurrentSession`, `getAccessToken`, `refreshSession`)
- **Single-Flight Refresh & Logout**: `refresh-manager.ts` deduplicates concurrent 401 refresh attempts; `performAppLogout()` (`mobile/src/auth/logout.ts`) revokes provider session, clears SecureStore tokens, and resets client state.
- **Verification**: `mobile/__tests__/phase09_2_auth.test.tsx` and `mobile/__tests__/phase09_9_exit_gate.test.tsx` pass in Jest. Live Supabase sandbox verification is `PENDING`.
