# 08 — Session Persistence

## Implementation
- `initializeAuthSession()` (`mobile/src/auth/logout.ts`) restores the active session via `authProviderService.getCurrentSession()` on startup and updates `useAuthStore`.
- Credentials are persisted in `expo-secure-store` (`WHEN_UNLOCKED_THIS_DEVICE_ONLY`), never in `AsyncStorage` or Zustand persistence.
- Account changes clear `queryClient` caches in `mobile/src/features/auth/authStore.ts` (`setMe`).
