# Search Product Freshness & Takedown Enforcement

## 1. Freshness Enforcement in Search
Search results must reflect real-time merchant inventory:
1. **Offer Verification**: Only offers with `status = 'ACTIVE'` and recent verification timestamps are eligible.
2. **Variant Invalidation**: When a variant SKU stock becomes `OUT_OF_STOCK`, the size filter query updates immediately.
3. **Stale Suppressing**: Listings not refreshed within the configured merchant sync window are marked `STALE` and suppressed from priority ranking.

---

## 2. Hard Takedown Exclusions
When a brand or rights holder files a takedown:
- `CatalogImageTakedown` status becomes `PROCESSING` or `COMPLETED`.
- All affected products and image assets are **immediately excluded** from search query execution plans.
- Active search sessions referencing the taken-down product ID invalidate the card before returning subsequent pages.
- Caches are purged synchronously.
