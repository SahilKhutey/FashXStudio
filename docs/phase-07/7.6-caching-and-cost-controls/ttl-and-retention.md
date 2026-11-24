# Cache TTL & Data Retention Policy

## 1. Lifecycle Overview

Virtual try-on results are subject to a dual-tier expiration policy balancing user experience against storage costs and privacy minimization:

| Asset Tier | Retention Period | Storage Location | Post-Expiry Action |
|---|---|---|---|
| **Rendered Try-On Images** | 7 Days | Private S3 Bucket | S3 Lifecycle deletion / tombstone |
| **Cache & Financial Metadata** | 30 Days | PostgreSQL Database | Archived to cold storage / pruned |

---

## 2. Temporal Calculation

Expiration timestamps are established upon successful storage of the result:

```python
expires_at = now + timedelta(days=7)
metadata_expires_at = now + timedelta(days=30)
```

### 2.1 Image Expiration (7 Days)
- When `now >= expires_at`:
  - `TryOnCacheService.get()` treats the entry as a cache miss (`reason="EXPIRED"`).
  - The record's status in `tryon_result_cache` is transitioned to `EXPIRED`.
  - An asynchronous object storage cleanup task or S3 lifecycle rule purges the underlying image bytes.

### 2.2 Metadata Retention (30 Days)
- Database metadata (`hit_count`, `last_hit_at`, `units_consumed`, cost metrics) is retained for 30 days to facilitate:
  - Monthly billing reconciliation with external providers.
  - Return on Investment (ROI) and cache savings analysis.
  - Debugging and support inquiries regarding shopper try-on history.
- After 30 days (`now >= metadata_expires_at`), records are safely pruned from the active OLTP database.
