# Full Snapshot Synchronization & Reconciliation

## 1. Overview and Invariant

A Full Synchronization captures an exhaustive point-in-time snapshot of an authorized merchant's active catalog.

### Strict Non-Negotiable Invariant: Safe Stale Reconciliation
> **A failed or partial full-sync run MUST NEVER mark existing products or offers as out-of-stock.**
> Missing offers may only be reconciled (marked out of stock) if the FULL sync completed **100% across all pages with zero uncaught exceptions**.

## 2. Ingestion and Snapshot Tracking

When running a full sync:
1. `CatalogSyncRun` is created in state `"running"` with `mode="full"`.
2. A unique snapshot tracking set (`seen_product_ids`) collects all source product IDs yielded by the adapter.
3. For each page fetched:
   - Items are normalized and upserted in the catalog database via `AcquisitionPipeline`.
   - The database transaction commits.
   - The cursor checkpoint is updated.
   - `CatalogSyncRun` metrics (`pages_fetched`, `products_seen`, `products_inserted`, `products_updated`) advance atomically.

## 3. Reconciliation Logic

Upon reaching the last page (`has_more == False`):
```python
if mode == SyncMode.FULL and all_success and apply and seen_product_ids:
    async with self.session_factory() as session:
        # Mark offers not seen in this snapshot as out of stock
        stale_stmt = (
            update(MerchantOffer)
            .where(
                MerchantOffer.merchant_id == source_record.merchant_id,
                MerchantOffer.source_product_id.not_in(seen_product_ids),
                MerchantOffer.in_stock.is_(True),
            )
            .values(in_stock=False)
        )
        await session.execute(stale_stmt)
        await session.commit()
```

If the run encounters any fatal exception midway:
- The run is marked `status="failed"`.
- The reconciliation query is **bypassed completely**.
- Existing products remain in their previously validated stock state, preventing catalog blackouts caused by transient provider hiccups.
