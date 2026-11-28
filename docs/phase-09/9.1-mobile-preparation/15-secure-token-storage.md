# 15 — Secure Token Storage

## Implementation (`mobile/src/auth/secureStorage.ts` & `session.ts`)
- Tokens (`accessToken`, `idToken`, `refreshToken`, `sub`) are stored via `expo-secure-store` with `SecureStore.WHEN_UNLOCKED_THIS_DEVICE_ONLY` (iOS Keychain / Android Keystore).
- `mobile/src/auth/stores/authStore.ts` stores only non-sensitive UI flags (`isAuthenticated`, `isLoading`, `userId`, `authError`) and zero tokens.
- `purgeLocalSession()` clears in-memory access token and deletes all SecureStore keys on logout.

## Verification
- `saveAuthTokens`, `getPersistedAccessToken`, `getPersistedRefreshToken`, and `clearAuthTokens` verified in `mobile/__tests__/phase09_1_foundation.test.ts` (mocked `SecureStore`). Physical-device Keychain/Keystore persistence remains `PENDING`.
