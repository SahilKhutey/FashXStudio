# 02 — Explore Search Architecture

- `mobile/app/(tabs)/explore.tsx` upgraded from client-side `useFeed()` filtering to `useProductSearch()` (`mobile/src/features/search/search.queries.ts`) calling `GET /api/v1/search/products` via `mobile/src/features/search/search.api.ts`.
- Uses `useDebouncedValue(filters.query, 350)` (`mobile/src/hooks/useDebouncedValue.ts`) and `AbortSignal` cancellation via TanStack Query.
