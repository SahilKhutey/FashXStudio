# RC07 — Mobile Integration Guide

## 1. Overview
The React Native / Expo mobile application (`mobile/`) integrates directly with the RC07 feed and behavioral signals endpoints.

## 2. Key Hooks & Components
- **File**: `mobile/src/features/feed/hooks.ts`
- **Hooks**:
  - `useFeed()`: Infinite query fetching paginated `/feed?cursor=...` records using TanStack React Query.
  - `useSignal()`: Mutation triggering `POST /feed/signals` with support for optimistic updates and a 5-second undo delay timer (`undoSignal`).
  - Cache Invalidation: Upon signal execution, `queryClient.invalidateQueries({ queryKey: ["feed"] })` ensures newly hidden items vanish immediately on next render.

## 3. Type Conformance
- `FeedResponse` aligns with `components["schemas"]["FeedResponse"]`.
- `FeedItem` aligns with `components["schemas"]["FeedItemResponse"]`.
- `FeedSignalResponse` aligns with `components["schemas"]["FeedSignalResponse"]`.

## 4. Verification
- TypeScript type-check: `npx --prefix mobile tsc -p mobile --noEmit` exits with **0 errors**.
- Jest mobile test suite: `npm --prefix mobile test -- --watchAll=false` runs **21 suites / 152 tests, 100% passing**.
