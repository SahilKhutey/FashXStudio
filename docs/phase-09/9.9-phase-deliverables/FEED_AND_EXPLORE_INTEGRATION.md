# Feed and Explore Integration

- **Search Client**: `searchProducts` and `getSearchFacets` (`mobile/src/features/search/search.api.ts`) query `/api/v1/search/products` and validate payloads with `ProductSearchResponseSchema`.
- **Debouncing & Cancellation**: `mobile/app/(tabs)/explore.tsx` uses `useDebouncedValue` and passes `AbortSignal` to cancel superseded in-flight searches.
- **Pagination Deduplication**: `flattenSearchPages` (`mobile/src/features/catalog/flatten-pages.ts`) deduplicates by `${item.product_id}:${item.merchant_product_id}`, removing duplicate page items while preserving multiple merchant offers for the same canonical product.
- **Verification**: `mobile/__tests__/phase09_4_discovery.test.tsx` and `mobile/__tests__/phase09_9_exit_gate.test.tsx` pass in Jest.
