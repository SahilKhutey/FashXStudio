# RC12: Catalog Operations and Freshness Monitoring

## 1. Objectives
Transform catalog ingestion from an unmonitored script into an auditable, continuously evaluated supply service ensuring product availability, clearance, and price freshness.

## 2. Ingestion & Validation Lifecycle
1. **Source Authorization**: Verify commercial feed agreement and image usage rights.
2. **Ingestion Run**: Fetch raw JSON/CSV feed snapshot; record `last_sync_utc`.
3. **Canonical Normalization**: Map partner product attributes into standardized fashion taxonomy.
4. **Duplicate Candidate Detection**: Flag multiple records sharing identical `source_product_id` or canonical barcodes.
5. **Freshness & Availability Check**: Verify price timestamp is $\le 24\text{ hours}$ old; flag out-of-stock items.
6. **Publication Gate**: Items failing clearance or freshness checks are excluded from discovery feeds.

## 3. Operational Health Metrics
Monitored via [`scripts/rc12/catalog_health.py`](file:///c:/Users/ASUS/Documents/FashXStudio/scripts/rc12/catalog_health.py):
- `total_fetched`: Ingested records count.
- `duplicate_candidates`: Duplicate IDs detected.
- `permission_blocked`: Items failing commercial rights check.
- `stale_prices`: Prices observed $>24\text{ hours}$ ago.
- `published_products`: Verified items active in discovery.
