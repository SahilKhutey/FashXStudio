# Mobile Architecture

- **Routing**: Expo Router file-based routes under `mobile/app/` (`(auth)/*`, `(tabs)/*`, `onboarding/*`, `products/[productId].tsx`, `tryon/capture.tsx`, `wardrobe/looks/create.tsx`).
- **Server State**: TanStack Query (`@tanstack/react-query`) manages catalog, PDP, profile, try-on polling, wardrobe items, and saved looks with user-scoped query keys (`wardrobeKeys.items(userId)`, `wardrobeKeys.looks(userId)`).
- **Client Transient State**: Zustand (`useOnboardingStore`, `useAppStore`) holds strictly in-memory UI/draft state and resets on onboarding completion and logout.
- **Networking**: Centralized `api()` wrapper in `mobile/src/api/client.ts` prepends `/api/v1`, injects `X-Request-ID` and `Idempotency-Key`, handles timeouts via `AbortController`, and executes single-flight 401 refresh on safe HTTP methods.
- **Environment Safety**: `mobile/src/config/environment.ts` validates `APP_ENV`, `EXPO_PUBLIC_API_BASE_URL`, and enforces HTTPS for `staging` and `production`.
