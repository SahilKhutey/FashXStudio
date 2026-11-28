# 24 — Phase 09.4 Release Checklist

- [x] Feed connected to `/api/v1/feed`
- [x] Explore connected to `/api/v1/search/products` with debounced query, sort, in-stock filter, and cursor pagination
- [x] `ProductSearchResponseSchema` Zod validation & `flattenSearchPages` offer-level deduplication
- [x] `PriceDisplay`, `ProductImage`, `EmptyProducts`, `ProductError`, and `isSafeMerchantUrl`
- [x] `tsc --noEmit`, `eslint --max-warnings 0`, and Jest suites pass locally
- [ ] Live staging catalog/search/takedown verification
- [ ] Physical Android & iOS device QA & performance benchmarks
