# 08 — Price Filters

- `validatePriceRange(minPrice, maxPrice)` (`mobile/src/features/search/search.filters.ts`) enforces non-negative bounds and `minPrice <= maxPrice`.
- `buildSearchQueryParams` sends `min_price`, `max_price`, and `currency` without silent cross-currency mixing.
