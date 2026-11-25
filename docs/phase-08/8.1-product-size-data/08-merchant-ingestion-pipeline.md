# 08 — Merchant Ingestion Pipeline

## 1. Ingestion Channels

Size data enters FashXStudio through three primary authorized channels:
1. **Direct Merchant REST API**: Authenticated merchant backend pushes via `POST /api/v1/products/{product_id}/size-chart`.
2. **Scheduled Feed Ingestion**: Periodic CSV/JSON catalog feeds processed via background workers.
3. **Partner Platform Adapters**: Webhook sync from Shopify, BigCommerce, or custom enterprise catalog exporters.

## 2. Ingestion Flow

```mermaid
sequenceDiagram
    participant Merchant as Merchant Backend
    participant IngestAPI as Catalog Ingestion API
    participant Validator as Size Validation Service
    participant Fingerprint as Fingerprint Calculator
    participant DB as Postgres (0056)
    participant Quarantine as Quarantine Table

    Merchant->>IngestAPI: POST /products/{id}/size-chart
    IngestAPI->>Validator: Validate Schema, Ranges & Category
    alt Validation Failed
        Validator-->>IngestAPI: Errors List
        IngestAPI->>Quarantine: Insert Quarantine Record (PENDING)
        IngestAPI-->>Merchant: 422 Unprocessable Entity (Validation Error)
    else Validation Passed
        Validator-->>IngestAPI: Validated Payload
        IngestAPI->>Fingerprint: Compute SHA-256
        Fingerprint-->>IngestAPI: Canonical Fingerprint
        IngestAPI->>DB: Compare with current_revision.fingerprint
        alt Fingerprint Identical
            IngestAPI->>DB: Log NO_OP_UNCHANGED event
            IngestAPI-->>Merchant: 200 OK (Existing Revision)
        else Fingerprint Differs
            IngestAPI->>DB: Deactivate old revision, insert v+1
            IngestAPI->>DB: Log VERSION_INCREMENTED event
            IngestAPI-->>Merchant: 201 Created (New Revision)
        end
    end
```

## 3. Idempotency Guarantees
Every submission is idempotent. Re-submitting the exact same chart data multiple times is guaranteed to create exactly one active revision.
