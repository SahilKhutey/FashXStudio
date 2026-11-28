# 04 — State Management

## Ownership Separation
- **Server State (`@tanstack/react-query`)**: Single shared `queryClient` in `mobile/src/app-shell/queryClient.ts` with `queryRetry` (retries only retryable `ApiError` up to 2 times; mutations never auto-retry).
- **Client UI State (`zustand`)**:
  - `mobile/src/stores/app.store.ts` (`useAppStore`): `selectedCategory`, `searchQuery`, `selectedColors`, `reset()`.
  - `mobile/src/auth/stores/authStore.ts`: Non-sensitive UI auth flags only (`isAuthenticated`, `isLoading`, `userId`, `authError`) — zero raw tokens.
  - Feature-scoped UI stores (`features/fit/store`, `features/fit-profile/store`, `features/profile/store`).
- **Auth Credentials**: Stored exclusively in `expo-secure-store` via `mobile/src/auth/secureStorage.ts`.

## Verification
- `useAppStore` category, search query, color selection, and `reset()` verified in `mobile/__tests__/phase09_1_foundation.test.ts`.
