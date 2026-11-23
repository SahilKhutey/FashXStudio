# Size and Availability Search Specification

## 1. Fashion Size Invariants
In fashion e-commerce, sizing availability is the number one driver of return rates and shopper dissatisfaction.
FashXStudio enforces three critical invariants:
1. **Source Evidence Only**: Sizing is derived strictly from verified merchant variant SKU records (`MerchantOfferSize` / `ProductVariant`). Sizes must **never be inferred** from product images, model heights, or generic category charts.
2. **Stock Verification**: A garment having a row in a size chart does not mean size M is in stock. Size filtering checks `merchant_offer_sizes.availability == 'IN_STOCK'`.
3. **Unknown is Not In-Stock**: If size stock is `UNKNOWN`, the system will not treat it as available when `in_stock=true` is requested.

---

## 2. Size Normalization Hierarchy
- Exact merchant size labels (e.g. `38`, `M`, `Medium`, `Free Size`) are preserved.
- Standard mappings (e.g. `Medium` $\rightarrow$ `M`) apply only where category rules support them.
- Numeric chest sizes (e.g. `38` in men's formal shirts) are distinct from letter sizes and are preserved.

---

## 3. Product Availability Lifecycle States

| State | Search Treatment |
| :--- | :--- |
| `IN_STOCK` | Fully eligible for normal search results. |
| `OUT_OF_STOCK` | Excluded when `in_stock=true` is requested. |
| `UNKNOWN` | Flagged as unverified; excluded if `in_stock=true`. |
| `DELISTED` / `DISCONTINUED` | Excluded completely from all shopper search queries. |
| `TAKEDOWN` | **Hard Exclusion**: Never served under any circumstances; immediate cache purge. |
| `STALE` | Suppressed if last verified timestamp exceeds freshness policy window. |
