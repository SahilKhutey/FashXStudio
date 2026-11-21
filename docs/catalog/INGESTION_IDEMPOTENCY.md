# Ingestion Idempotency

## 1. Idempotency Guarantees

The FashXStudio catalog ingestion pipeline guarantees end-to-end idempotency:

1. **Re-executing the Same Batch**: Ingesting an identical batch of records repeatedly produces zero duplicate garments, offers, or image rows.
2. **Crash Resilience**: If a worker crashes mid-batch, re-running the batch updates `last_seen_at` without duplicating products or corrupting offers.
3. **Quarantine Idempotency**: Re-encountering an invalid product does not spam the quarantine table; it safely upserts against `(source_id, source_product_id, reason_code)`.

---

## 2. Ingestion Change Matrix

| State in DB | Incoming State | Action Taken | Metric Counter |
| :--- | :--- | :--- | :--- |
| Non-existent | Valid Product | Insert `CanonicalGarment`, `MerchantProduct`, `MerchantOffer` | `inserted` +1 |
| Exists | Identical hash, price, stock | Update `last_seen_at` and `last_synced_at` | `unchanged` +1 |
| Exists | Changed hash or price | Update garment attributes and offer price | `updated` +1 |
| Any | Validation failure | Insert/Update `catalog_ingestion_quarantine` | `quarantined` +1, `rejected` +1 |
