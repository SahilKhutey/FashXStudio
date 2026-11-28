# 07 — Category Filters

- `buildSearchQueryParams` passes `category_id` to `/api/v1/search/products`; `useSearchFacets` (`getSearchFacets`) queries `/api/v1/search/facets` with `staleTime: 5 * 60_000`.
