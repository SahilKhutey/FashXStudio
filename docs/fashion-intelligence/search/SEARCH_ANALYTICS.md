# Search Analytics & Interaction Recording

## 1. Objectives
Track search quality, friction points, filter usage, and conversion drop-offs without invading shopper privacy or violating DPDP compliance.

---

## 2. Event Model (`product_search_events`)
Events recorded during shopper journeys:
- `SEARCH_SUBMITTED`: Fired when a new search query is executed.
- `SEARCH_RESULTS_RETURNED`: Records total result count, query latency (ms), and active filters.
- `SEARCH_FILTER_APPLIED`: Fired when a shopper adds a category, brand, size, or price filter.
- `SEARCH_FILTER_REMOVED`: Fired when a filter is removed.
- `SEARCH_RESULT_CLICKED`: Records the product ID, rank position (1-based), and session token.
- `SEARCH_PRODUCT_SAVED`: Shopper saved product to wishlist/wardrobe from search results.
- `SEARCH_NO_RESULTS`: Zero items matched query; triggers diagnostic review.
- `SEARCH_MERCHANT_HANDOFF`: Shopper clicked "Buy on Merchant" outbound referral link.

---

## 3. Privacy Boundaries
- Raw search logs do not record IP addresses or personal names.
- Analytics events link to `search_sessions` and `user_id` (pseudonymous UUID) only.
