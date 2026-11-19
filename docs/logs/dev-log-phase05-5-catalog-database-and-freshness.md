# Dev Log: Phase 05.5 — Catalog Database and Freshness

- Date: 2026-11-19
- Author: Antigravity Assistant
- Area: Catalog Database, Provenance, Freshness, and Query Optimization

## Architectural Context
Phase 05.5 establishes a data layer distinguishing product identity (`CanonicalGarment`), merchant listings (`MerchantProduct`), and commercial offers (`MerchantOffer`). A single shirt sold by multiple retailers can have separate prices, availability states, and synchronization histories without losing canonical identity.

## Changes Implemented
1. **Database Schema & Migrations**:
   - `0042_add_catalog_database_and_freshness.py`
   - Added tables: `size_definitions`, `product_variants`, `merchant_offer_sizes`, `merchant_offer_price_history`, `catalog_provenance_records`.
   - Added composite and lookup indexes for category/brand discovery, price filtering, offer status, and source identity.
2. **Backend Domain & Services**:
   - `backend/fashx/catalog/freshness/models.py`: Freshness policies and `calculate_freshness()`.
   - `backend/fashx/catalog/freshness/service.py`: `CatalogFreshnessService` evaluating freshness states and recording non-duplicate price observations.
   - `backend/fashx/catalog/freshness/reconciliation.py`: `CatalogReconciliationService` fail-closed snapshot reconciliation.
   - `backend/fashx/catalog/freshness/query_service.py`: `CatalogQueryService` multi-factor indexed search.
   - `backend/fashx/catalog/freshness/provenance_service.py`: `CatalogProvenanceService`.
3. **Repository Layer**:
   - Added repositories to `backend/fashx/catalog/repositories/catalog_repository.py`:
     - `MerchantOfferPriceHistoryRepository`
     - `SizeDefinitionRepository`
     - `ProductVariantRepository`
     - `MerchantOfferSizeRepository`
     - `CatalogProvenanceRepository`
     - Connected as properties on `CatalogUnitOfWork`.
4. **Acquisition Pipeline Integration**:
   - `pipeline.py` updated to populate `merchant_product_id`, `source_id`, `ingest_run_id`, `first_ingested_at`, `last_ingested_at`, `last_verified_at`, and record price history on price changes.
   - Takedown protection implemented to block reactivation of products under takedown.
5. **Schema Inspection Utility**:
   - `scripts/inspect_catalog_schema.py` inspecting all tables, columns, indexes, and validating all Phase 05.5 invariants.
