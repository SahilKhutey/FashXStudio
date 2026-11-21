# Ingestion Error Handling

## 1. Error Classification & Stratification

Errors in the catalog ingestion pipeline are stratified into three tiers:

| Error Tier | Examples | Impact | Pipeline Action |
| :--- | :--- | :--- | :--- |
| **System / Source Fatal** | Unregistered source, unverified merchant, suspended source, missing `PRODUCT_DATA_STORE` | Entire run aborted | Mark `IngestRun` status `REJECTED`, rollback transaction, emit alert. |
| **Record Validation Fatal** | Missing `source_product_id`, invalid price, non-HTTPS URL, unmapped category | Record rejected | Quarantine record, increment `rejected` and `quarantined`, proceed to next record. |
| **Asset / Partial Warning** | Image fetch 404, image display permission denied | Record persisted without asset | Ingest product metadata, mark `display_eligible=False`, log metric. |

---

## 2. Terminal Run Statuses

- **`COMPLETED`**: All records validated, normalized, and persisted successfully.
- **`PARTIAL`**: Some valid records persisted, while some invalid records were quarantined.
- **`REJECTED`**: Source authorization failed, or all records in the batch failed validation/mapping.
- **`FAILED`**: Unhandled system exception or database connectivity loss.
- **`ABORTED`**: Ingestion explicitly cancelled via administrative endpoint or mid-run takedown.
