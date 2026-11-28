# 03 — Navigation Architecture

## Route Structure (`mobile/app/`)
- `_layout.tsx`: Root `AppProviders` (`QueryClientProvider`), remote config & version/maintenance gate, auth session restoration, and route-policy enforcement.
- `(auth)/`: `sign-in.tsx`, `verify.tsx`, `dev-token.tsx` (unauthenticated routes; blocked in production for dev-token).
- `(gates)/`: `maintenance.tsx`, `update-required.tsx`.
- `onboarding/`: `consent.tsx`, `profile.tsx`, `quiz.tsx`, `capture.tsx`.
- `(tabs)/`: `feed.tsx`, `explore.tsx`, `looks.tsx`, `closet.tsx`.
- Detail / Workflow routes: `garment/[id].tsx`, `tryon/[jobId].tsx`, `settings/index.tsx`.

## Route Policy (`mobile/src/navigation/route-policy.ts`)
- `getRouteDecision` enforces fail-closed authentication and onboarding completion (`consent` -> `profile` -> `style_quiz` -> `photo`).
- Unauthenticated users cannot enter `(tabs)` or detail routes and are redirected to `/(auth)/sign-in`.
- Verified by `mobile/src/navigation/__tests__/route-policy.test.ts`.
