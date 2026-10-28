# P3 — Application Shell and Navigation
Project: FashXStudio  
Milestone: P3  
Status: Implemented

## Objective
Create a consistent application shell around the existing Expo Router application while preserving authentication, onboarding, remote configuration, and feature navigation.

## Deliverables
1. **Shared screen container with safe-area support** (`mobile/src/app-shell/ScreenContainer.tsx`):
   - Integrates `react-native-safe-area-context` with configurable padding and scroll behaviors.
   - Automatically adapts background and layout padding using design system tokens.
2. **Consistent navigation theme and tab presentation** (`mobile/app/(tabs)/_layout.tsx`, `mobile/src/navigation/navigation-theme.ts`):
   - Centralizes colors, typography, touch targets, and spacing from the P2 design tokens.
   - Preserves verified `/settings` header shortcut navigation and tabs (feed, looks, closet).
3. **Testable authentication and onboarding route policy** (`mobile/src/navigation/route-policy.ts`):
   - Decoupled functional router policy (`getRouteDecision`) governing authentication gates and sequential onboarding progression.
   - Comprehensive test suite in `mobile/src/navigation/__tests__/route-policy.test.ts`.
4. **Shared loading, empty, and error states** (`mobile/src/components/states/`):
   - `LoadingState`: full-screen or compact spinner with accessibility roles.
   - `ErrorState`: actionable error display with accessible retry callback.
   - `EmptyState`: context-aware placeholder with optional icon and action button.
5. **Incremental migration of feed, try-on history (looks), and closet screens**:
   - `mobile/app/(tabs)/feed.tsx`: consumes `LoadingState`, `ErrorState`, and `EmptyState`.
   - `mobile/app/(tabs)/looks.tsx`: consumes shared states and semantic status color tokens.
   - `mobile/app/(tabs)/closet.tsx`: consumes shared states and semantic styling tokens.
6. **Application providers and status bar** (`mobile/src/app-shell/AppProviders.tsx`, `mobile/src/app-shell/AppStatusBar.tsx`):
   - Initialized at root level in `mobile/app/_layout.tsx`, managing query client and theme-reactive status bar.

## Architectural constraints & adherence
- **Expo Router preserved**: No secondary navigation library introduced; standard file-based routing maintained.
- **Zustand & React Query preserved**: Authentication store and global query cache policies intact.
- **Fail-closed gates preserved**: Remote configuration maintenance mode and minimum-version checks remain operational.
- **Design Token System**: All shell and state components consume tokens from `mobile/src/design-system/`.

## Acceptance checklist
- [x] Root providers initialized exactly once (`AppProviders` in `mobile/app/_layout.tsx`).
- [x] Authentication and onboarding redirects do not loop (verified via `route-policy.test.ts`).
- [x] Existing routes remain valid (`(auth)`, `onboarding`, `(tabs)`, `settings`, `garment`, `tryon`).
- [x] Navigation labels and accessibility roles present across all states.
- [x] Shared loading, empty, and error states integrated into tabs.
- [x] Retry actions call corresponding refetch operations.
- [x] TypeScript checks (`tsc --noEmit`), ESLint (`eslint . --max-warnings 0`), and Jest suites pass.
- [x] Android production export bundling (`expo export --platform android`) compiles without errors.
