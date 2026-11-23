# Incremental Synchronization Architecture

## 1. Overview and Rationale

Full catalog synchronization can be resource-intensive for large retailers with tens of thousands of garments. Incremental synchronization retrieves only apparel products that have been created, modified, or deactivated since the previous successful sync run.

## 2. Watermark Mechanics

Incremental sync operates against the `catalog_sync_checkpoints` table:
- **`checkpoint_type`**: Set to `"incremental"`.
- **`watermark`**: Timestamp representing the provider's `last_updated` point.
- **`cursor_data`**: JSON object containing pagination continuation tokens for in-progress delta runs.

### Flow:
1. `CatalogSyncEngine.execute_sync(source_id, adapter, mode=SyncMode.INCREMENTAL)` is invoked.
2. The engine loads the latest checkpoint for the source.
3. The adapter's `fetch_page(cursor=initial_cursor, limit=limit)` retrieves changed records.
4. If supported by the adapter and provider, query parameters like `updated_after={watermark.isoformat()}` are passed to filter unchanged items.
5. Ingestion pipeline normalizes and updates `MerchantProduct` and `MerchantOffer` records idempotently.
6. The new watermark and checkpoint are committed.

## 3. Atomic Progress Tracking

During incremental sync:
- The database transaction containing the product changes is committed **first**.
- Next, `SyncCheckpointManager.save_checkpoint()` advances the watermark timestamp to `datetime.now(UTC)`.
- If a network error or worker restart occurs midway, the checkpoint holds the last successfully committed page cursor, allowing exact resume without data duplication.
