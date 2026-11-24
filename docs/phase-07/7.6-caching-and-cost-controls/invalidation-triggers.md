# Cache Invalidation Triggers & Lifecycle Management

## 1. Overview

While caching reduces costs, serving a stale or revoked result violates legal and business compliance:
- If a merchant updates a garment photograph to fix a styling flaw, customers must not receive try-ons with the outdated design.
- If an item is delisted or subject to a copyright/DMCA takedown, all try-on renders showing that item must immediately cease being served.
- If a shopper revokes photo processing consent under GDPR/CCPA, their cached outputs must be revoked and permanently scheduled for deletion.

---

## 2. Invalidation Taxonomy

| Reason Code | Trigger Event | Scope | Action |
|---|---|---|---|
| `PRODUCT_IMAGE_CHANGED` | Merchant updates garment catalog asset | Product ID | Transitions active cache entries for product to `INVALIDATED`. |
| `PRODUCT_TAKEDOWN` | DMCA / legal takedown request accepted | Product ID | Immediate invalidation; blocks presigned download generation. |
| `MERCHANT_DELISTED` | Merchant suspends account or archives item | Product ID | Invalidation; cached records ineligible for reuse. |
| `CONSENT_WITHDRAWN` | Shopper revokes photo processing consent | User ID | Invalidates all user's cache records; schedules S3 asset purge. |
| `SHOPPER_DELETED` | Account deletion workflow triggered | User ID | Hard delete/purge of cache records and underlying artifacts. |
| `PROVIDER_CONFIG_CHANGED` | FASHN model or pipeline upgraded | Provider / Model | Invalidates entries to force re-render with higher fidelity. |
| `MANUAL_PURGE` | Ops/support administrative override | Cache Key | Targeted invalidation of an individual corrupted render. |

---

## 3. Database Execution Pattern

Invalidations update the `tryon_result_cache` table atomically:

```sql
UPDATE tryon_result_cache
SET status = 'INVALIDATED',
    invalidation_reason = 'PRODUCT_TAKEDOWN: Notice #1042',
    updated_at = NOW()
WHERE canonical_product_id = :product_id
  AND status = 'ACTIVE';
```

Subsequent lookup queries with `status = 'ACTIVE'` automatically bypass invalidated records, falling back to fresh inference (or failing at the authorization gate if the product is under takedown).
