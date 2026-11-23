# Product Persistence Policy

## 1. Relational Persistence Workflow

The catalog persistence policy defines how entities are written to PostgreSQL:

1. **Transactional Unit of Work**: Ingestion operates via `CatalogUnitOfWork(session_factory)` ensuring ACID transactions.
2. **Deterministic Upsert Order**:
   - `CanonicalGarment` is flushed first to establish foreign key `garment.id`.
   - `MerchantProduct` is inserted or updated linking `canonical_garment_id`.
   - `MerchantOffer` is synchronized with current price and availability.
   - Authorized images are persisted to `garment_images`.
3. **Commit Boundaries**:
   - Each batch commits cleanly. If an unhandled database exception occurs, the transaction rolls back, and no partial product mutations leak.

---

## 2. Invariant: Absence Is Not Deletion

- An empty batch, network error, or feed drop during an incremental sync must **never** delete or deactivate previously ingested products.
- Out-of-stock reconciliation occurs strictly via explicit full-sync processes (`FullSyncSession`) after verified completion of all pages.
