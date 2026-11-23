# Phase 06.2 — Catalog Admin Enrichment API Contracts

## 1. Endpoints Overview

All endpoints are mounted under `/api/v1/admin/catalog`.

### 1.1 Queue Enrichment
- **Method**: `POST`
- **Path**: `/products/{product_id}/enrich`
- **Response**: `200 OK`
```json
{
  "run_id": "8bbdc134-2975-4720-bc21-0c587cba55be",
  "product_id": "0d6110f0-8c92-4919-974a-e465053cfd11",
  "status": "QUEUED",
  "message": "Enrichment job queued"
}
```

### 1.2 Get Enrichment Run Status
- **Method**: `GET`
- **Path**: `/enrichment-runs/{run_id}`
- **Response**: `200 OK`
```json
{
  "run_id": "8bbdc134-2975-4720-bc21-0c587cba55be",
  "product_id": "0d6110f0-8c92-4919-974a-e465053cfd11",
  "status": "COMPLETED",
  "attempt_number": 1,
  "started_at": "2026-11-20T05:00:00Z",
  "completed_at": "2026-11-20T05:00:02Z",
  "error_code": null
}
```

### 1.3 Get Current Product Enrichment
- **Method**: `GET`
- **Path**: `/products/{product_id}/enrichment`
- **Response**: `200 OK`

### 1.4 Retry Failed Enrichment Run
- **Method**: `POST`
- **Path**: `/enrichment-runs/{run_id}/retry`

### 1.5 List Pending Reviews
- **Method**: `GET`
- **Path**: `/reviews`
- **Query Params**: `merchant_id` (optional UUID)

### 1.6 Submit Review Decision
- **Method**: `POST`
- **Path**: `/reviews/{review_id}/decision`
- **Body**:
```json
{
  "action": "APPROVE",
  "corrected_value": null,
  "reason": "Confirmed navy shade in visual swatch"
}
```
