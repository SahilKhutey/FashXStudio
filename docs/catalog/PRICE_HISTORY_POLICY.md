# Price History Policy

## 1. Storage Rules
1. Price history is append-only in `merchant_offer_price_history`.
2. Amounts are stored in integer minor units (`price_minor: BIGINT`) alongside ISO 4217 currency (`currency: CHAR(3)`).
3. A new price observation is inserted **only** when the effective price or currency changes.
4. Routine feed syncs that observe an unchanged price update `last_price_verified_at` and `last_verified_at` on `merchant_offers` without inserting duplicate history rows.
5. Missing prices are never interpreted as zero.
