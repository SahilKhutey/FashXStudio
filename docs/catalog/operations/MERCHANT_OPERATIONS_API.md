# Merchant Operations API Reference

## 1. Overview
The Merchant Operations API exposes control plane capabilities for FashXStudio catalog acquisition. All merchant endpoints require bearer token authentication and enforce tenant isolation.

---

## 2. Merchant Operational Endpoints

### 2.1 Connect Catalog Source
- **Endpoint**: `POST /api/v1/merchant/sources`
- **Headers**: `Authorization: Bearer <token>`, `X-Merchant-ID: <uuid>`
- **Request Body**:
  ```json
  {
    "merchant_id": "07eeb43d-74b2-4fd2-a62c-0071f41bd144",
    "slug": "nordic-knitwear-api",
    "name": "Nordic Knitwear API",
    "source_type": "MERCHANT_API",
    "adapter_name": "generic_merchant_api",
    "access_method": "API_KEY",
    "credential_secret_ref": "secrets://fashx-prod/keys/api-key",
    "refresh_hours": 24
  }
  ```
- **Response**: `201 Created`
  ```json
  {
    "id": "2f377a40-8d73-4540-ba6d-2268844f28f4",
    "merchant_id": "07eeb43d-74b2-4fd2-a62c-0071f41bd144",
    "slug": "nordic-knitwear-api",
    "name": "Nordic Knitwear API",
    "source_type": "MERCHANT_API",
    "adapter_name": "generic_merchant_api",
    "adapter_version": "1.0.0",
    "access_method": "API_KEY",
    "masked_credential_ref": "secrets://fashx-prod/keys/******",
    "source_status": "PENDING_REVIEW",
    "operational_status": "ENABLED",
    "is_enabled": true,
    "created_at": "2026-11-19T10:00:00Z"
  }
  ```

---

### 2.2 Get Sync Status Dashboard
- **Endpoint**: `GET /api/v1/merchant/sources/{source_id}/status`
- **Response**: `200 OK`
  ```json
  {
    "source_id": "2f377a40-8d73-4540-ba6d-2268844f28f4",
    "source_name": "Nordic Knitwear API",
    "operational_status": "ENABLED",
    "source_status": "AUTHORIZED",
    "last_sync_status": "ok",
    "last_sync_mode": "INCREMENTAL",
    "last_successful_sync_at": "2026-11-19T09:30:00Z",
    "duration_seconds": 45.2,
    "counts": {
      "fetched": 150,
      "inserted": 30,
      "updated": 120,
      "quarantined": 0
    },
    "is_healthy": true
  }
  ```

---

### 2.3 Update Operational Status (Enable / Disable)
- **Endpoint**: `PATCH /api/v1/merchant/sources/{source_id}/operational-status`
- **Request Body**:
  ```json
  {
    "target_status": "DISABLED",
    "reason": "Temporary feed pause for maintenance"
  }
  ```
- **Response**: `200 OK`
  ```json
  {
    "source_id": "2f377a40-8d73-4540-ba6d-2268844f28f4",
    "operational_status": "DISABLED",
    "is_enabled": false,
    "updated_at": "2026-11-19T10:05:00Z",
    "message": "Source operational status set to DISABLED. 1 running jobs aborted."
  }
  ```

---

### 2.4 Trigger Manual Synchronization
- **Endpoint**: `POST /api/v1/merchant/sources/{source_id}/sync`
- **Request Body**:
  ```json
  {
    "sync_mode": "INCREMENTAL",
    "idempotency_key": "sync-req-12345",
    "force": false
  }
  ```
- **Response**: `200 OK`
  ```json
  {
    "run_id": "a91b2c3d-4e5f-6a7b-8c9d-0e1f2a3b4c5d",
    "source_id": "2f377a40-8d73-4540-ba6d-2268844f28f4",
    "sync_mode": "INCREMENTAL",
    "status": "queued",
    "idempotency_key": "sync-req-12345",
    "is_duplicate_request": false,
    "enqueued_at": "2026-11-19T10:10:00Z"
  }
  ```

---

### 2.5 Configure Synchronization Schedule
- **Endpoint**: `PUT /api/v1/merchant/sources/{source_id}/schedule`
- **Request Body**:
  ```json
  {
    "enabled": true,
    "sync_mode": "INCREMENTAL",
    "interval_minutes": 120,
    "timezone": "Asia/Kolkata"
  }
  ```
- **Response**: `200 OK`
  ```json
  {
    "id": "e1f2a3b4-c5d6-7e8f-9a0b-1c2d3e4f5a6b",
    "source_id": "2f377a40-8d73-4540-ba6d-2268844f28f4",
    "merchant_id": "07eeb43d-74b2-4fd2-a62c-0071f41bd144",
    "enabled": true,
    "sync_mode": "INCREMENTAL",
    "interval_minutes": 120,
    "timezone": "Asia/Kolkata",
    "next_run_at": "2026-11-19T12:00:00Z",
    "updated_at": "2026-11-19T10:00:00Z"
  }
  ```

---

### 2.6 Query Ingestion Failures
- **Endpoint**: `GET /api/v1/merchant/sources/{source_id}/errors?page=1&page_size=50`
- **Response**: `200 OK` (All bearer tokens and API keys redacted to `******`)

---

### 2.7 Query Quarantined Records
- **Endpoint**: `GET /api/v1/merchant/sources/{source_id}/quarantine?status=PENDING`
- **Response**: `200 OK` (Enriched with `guidance` detailing remediation actions)

---

### 2.8 Get Image Permission Matrix
- **Endpoint**: `GET /api/v1/merchant/sources/{source_id}/image-permissions`
- **Response**: `200 OK`
  ```json
  {
    "source_id": "2f377a40-8d73-4540-ba6d-2268844f28f4",
    "merchant_id": "07eeb43d-74b2-4fd2-a62c-0071f41bd144",
    "fetch_permitted": true,
    "store_permitted": true,
    "display_permitted": true,
    "ai_processing_permitted": true,
    "vto_permitted": true,
    "derivatives_retained": true,
    "total_assets_count": 420,
    "active_assets_count": 418,
    "suspended_assets_count": 2,
    "warning_messages": []
  }
  ```

---

### 2.9 Override Product Field
- **Endpoint**: `POST /api/v1/merchant/products/{product_id}/override`
- **Request Body**:
  ```json
  {
    "field_name": "title",
    "override_value": {"value": "Super Linen Premium Shirt"},
    "reason": "Editorial title upgrade"
  }
  ```
- **Response**: `200 OK`

---

### 2.10 Deactivate Merchant Offer
- **Endpoint**: `POST /api/v1/merchant/offers/{offer_id}/deactivate`
- **Request Body**:
  ```json
  {
    "reason": "End of seasonal stock"
  }
  ```
- **Response**: `200 OK`
  ```json
  {
    "offer_id": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
    "merchant_id": "07eeb43d-74b2-4fd2-a62c-0071f41bd144",
    "garment_id": "f1e2d3c4-b5a6-7f8e-9d0c-1b2a3f4e5d6c",
    "offer_status": "INACTIVE",
    "canonical_garment_active": true,
    "deactivated_at": "2026-11-19T10:15:00Z"
  }
  ```

---

## 3. Platform Admin Operational Endpoints

### 3.1 Emergency Source Takedown
- **Endpoint**: `POST /api/v1/admin/sources/{source_id}/takedown`
- **Authorization**: `require_role("admin")`
- **Request Body**:
  ```json
  {
    "reason_code": "LEGAL_TAKEDOWN",
    "reason_text": "Immediate takedown per DMCA / legal notice ref #8821",
    "purge_images": true
  }
  ```
- **Response**: `200 OK`
  ```json
  {
    "source_id": "2f377a40-8d73-4540-ba6d-2268844f28f4",
    "takedown_status": "COMPLETED",
    "jobs_cancelled_count": 2,
    "offers_deactivated_count": 142,
    "images_purged_count": 420,
    "completed_at": "2026-11-19T10:20:00Z"
  }
  ```
