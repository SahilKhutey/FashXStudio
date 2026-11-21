# Ingestion Observability

## 1. Metrics and Telemetry

Ingestion jobs emit detailed operational metrics stored in the `IngestRun.counts` JSON payload and surfaced via admin endpoints:

- `total`: Total records received from the source adapter.
- `validated`: Records that passed schema and taxonomy checks.
- `inserted`: Novel products added to the catalog.
- `updated`: Existing products modified with new attributes or pricing.
- `unchanged`: Existing products refreshed with updated `last_seen_at`.
- `rejected`: Records rejected due to validation failure or missing rights.
- `quarantined`: Records stored in `catalog_ingestion_quarantine`.
- `image_counts`: Breakdown of `permitted`, `skipped_by_permission`, `missing`, and `stored` assets.

---

## 2. Administrative REST Endpoints

Mounted on `/api/v1/admin/catalog/`:

- `POST /ingestion-jobs`: Trigger on-demand catalog ingestion.
- `GET /ingestion-jobs/{run_id}`: Inspect run state, status, and execution metadata.
- `GET /ingestion-jobs/{run_id}/report`: Full JSON report containing counters and rejection reasons.
- `POST /ingestion-jobs/{run_id}/cancel`: Abort an active ingestion execution.
- `GET /quarantine`: List quarantined records with pagination and source/status filtering.
- `GET /quarantine/{quarantine_id}`: Detailed inspection of a specific quarantined item.
- `POST /quarantine/{quarantine_id}/reprocess`: Trigger re-validation and ingestion of a quarantined record.
