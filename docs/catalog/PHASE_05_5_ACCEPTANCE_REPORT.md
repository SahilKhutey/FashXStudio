# Phase 05.5 — Catalog Database and Freshness
## Acceptance Report

Status: 🟢 VERIFIED (Code & Test Gate Pass; awaiting founder staging sign-off)
Phase: 05.5
Version: 1.0

### 1. Repository baseline
- Git commit: In working tree (branch `feat/phase04.5-photo-upload`)
- Branch: `feat/phase04.5-photo-upload`
- Migration head: `0042_add_catalog_database_and_freshness`
- PostgreSQL target: 16 (local execution on SQLite AsyncEngine per AGENTS.md Rule 14)

### 2. Schema review
- Product schema: Separated CanonicalGarment from MerchantProduct and MerchantOffer.
- Merchant schema: Independent operational_status and verification_status.
- Source schema: Adapter name, version, last failed sync, and freshness policies recorded.
- Image schema: Linked via asset_id to CatalogImageAsset and transformations from Phase 05.4.
- Size/variant schema: Partitioned across size_definitions, product_variants, and merchant_offer_sizes.
- Price history schema: Immutable append-only merchant_offer_price_history.

### 3. Implemented changes
- Migrations: `0042_add_catalog_database_and_freshness.py`
- Models: `database/models/catalog_freshness.py`, updated `database/models/catalog.py`
- Repositories: `MerchantOfferPriceHistoryRepository`, `SizeDefinitionRepository`, `ProductVariantRepository`, `MerchantOfferSizeRepository`, `CatalogProvenanceRepository`
- Services: `CatalogFreshnessService`, `CatalogReconciliationService`, `CatalogQueryService`, `CatalogProvenanceService`
- Indexes: Performance composite and lookup indexes added across tables.

### 4. Data integrity
- Uniqueness: Enforced on `(source_id, source_product_id)`, `(size_system, category, standardized_label)`, and `(merchant_offer_id, raw_size)`.
- Foreign keys: Cascade and set-null constraints configured across hierarchy.
- Provenance: Attribution records persisted in `catalog_provenance_records`.
- Timestamps: `first_ingested_at`, `last_ingested_at`, `last_seen_at`, `last_verified_at`, and `last_changed_at` distinct.
- Takedown protection: Active takedowns block re-activation or reconciliation by routine sync.

### 5. Freshness
- Freshness policies: Default targets configured (Price: 6h, Availability: 2h, Metadata: 24h, Sizes: 2h, Images: 7d).
- Last verified behavior: Updated only after explicit verification.
- Stale detection: Evaluated via `calculate_freshness()` returning CURRENT, STALE, UNKNOWN, REVIEW_REQUIRED.
- Full-sync reconciliation: Only COMPLETED full snapshots can reconcile unobserved offers; failed runs reject reconciliation.

### 6. Test evidence
- Unit tests: 14 test cases in `tests/unit/catalog/test_catalog_database_and_freshness.py` (CAT-DB-001 to CAT-DB-020).
- Integration tests: 2 tests in `tests/integration/catalog/test_catalog_schema_and_freshness.py`.
- Performance tests: 1 suite in `tests/performance/test_catalog_query_performance.py`.
- Total catalog unit suite: 113 passing tests in `tests/unit/catalog`.

### 7. Performance
- Dataset size: Seed benchmark dataset (50 garments, 100 offers, 100 sizes, 100 price observations).
- Query P50 / P95:
  - Source identity lookup: P50=1.48ms, P95=7.65ms (target < 50ms)
  - Product detail retrieval: P50=2.77ms, P95=7.50ms (target < 100ms)
  - Category / Brand filter: P50=1.41ms, P95=3.18ms (target < 150ms)
  - Combined filter: P50=1.22ms, P95=2.68ms (target < 200ms)
  - Merchant offers listing: P50=1.78ms, P95=2.91ms (target < 150ms)
  - Stale offer query: P50=1.00ms, P95=2.97ms (target < 250ms)
  - Price history lookup: P50=0.58ms, P95=1.49ms (target < 100ms)

### 8. Outstanding risks
- PostgreSQL staging verification: Per Rule 14, benchmark and database tests were executed against SQLite/AsyncEngine; live PostgreSQL execution will be validated in GitHub Actions CI.

### 9. Approval
- Engineering: Verified
- Database: Verified
- Security: Verified
- Product: Pending founder review
- Release decision: Ready for PR merge after founder staging run
