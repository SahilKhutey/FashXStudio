# 10 — Logout

## Implementation (`mobile/src/auth/logout.ts`)
- `performAppLogout()` coalesces concurrent logout requests into a single in-flight promise.
- Calls `authProviderService.logout()`, and in `finally` unconditionally executes:
  - `purgeLocalSession()` (in-memory token + SecureStore keys)
  - `queryClient.clear()`
  - `useAppStore.getState().reset()`
  - `useFeatureAuthStore.getState().signOut()`
  - `useUiAuthStore.getState().setUnauthenticated()`
- Offline or remote revocation errors never leave local credentials or cached account data intact.
