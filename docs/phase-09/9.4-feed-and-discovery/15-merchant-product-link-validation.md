# 15 — Merchant Product Link Validation

- `isSafeMerchantUrl()` (`mobile/src/features/catalog/utils/product-links.ts`) permits only `https:` outbound URLs and rejects `http:`, `javascript:`, or malformed URLs.
- Feed and Explore navigate to internal detail routes (`/garment/{id}`) before any outbound merchant handoff.
