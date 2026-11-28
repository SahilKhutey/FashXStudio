# 12 — Pagination

- Cursor pagination via `useInfiniteQuery` (`next_cursor`) with `onEndReachedThreshold={0.5}` and `isFetchingNextPage` guard.
- `flattenSearchPages()` (`mobile/src/features/catalog/flatten-pages.ts`) deduplicates by `${product_id}:${merchant_product_id}` so separate merchant offers for the same product are preserved.
