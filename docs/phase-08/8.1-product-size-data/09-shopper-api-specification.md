# 09 — Shopper API Specification

## 1. Endpoints Overview

All sizing and availability endpoints are exposed under `/api/v1/products`.

### 1.1 `GET /api/v1/products/{product_id}/size-chart`
Fetches the active size chart for a product.

**Query Parameters:**
- `unit` (optional): Preferred measurement unit (`CM`, `INCH`).
- `system` (optional): Preferred sizing system code (e.g., `US`, `UK`, `EU`).

**Success Response (Verified Chart Available):**
```json
{
  "chart_id": "8f8b89d6-5864-4e4b-91f9-813c9e99a80b",
  "merchant_product_id": "d3b07384-d113-40f7-b08e-1616f7311ed1",
  "merchant_id": "4a73e654-7935-4dbb-80a2-fb9f82650f9d",
  "version": 1,
  "content_fingerprint": "a3b1c2d3...",
  "size_system": {
    "code": "INTL_ALPHA",
    "system_type": "REGIONAL_STANDARD",
    "display_name": "International Alpha",
    "mapping_status": "NATIVE"
  },
  "measurement_basis": "GARMENT",
  "display_unit": "CM",
  "status": "AVAILABLE",
  "is_stale": false,
  "provenance": {
    "source_id": "MERCHANT_DIRECT",
    "source_revision": "rev_2026_01",
    "retrieved_at": "2026-11-25T10:00:00Z",
    "verified_at": "2026-11-25T10:00:00Z"
  },
  "rows": [
    {
      "merchant_size": "M",
      "mapped_size": null,
      "sort_order": 1,
      "measurements": [
        {
          "field_code": "CHEST",
          "display_name": "Chest",
          "value": 100.0,
          "unit": "CM",
          "normalized_cm": 100.0
        }
      ]
    }
  ],
  "last_verified_at": "2026-11-25T10:00:00Z"
}
```

**Success Response (No Verified Chart):**
Returns HTTP 200 with an explicit unavailable payload (never 404 for existing products):
```json
{
  "product_id": "d3b07384-d113-40f7-b08e-1616f7311ed1",
  "status": "UNAVAILABLE",
  "message": "Verified merchant size chart is unavailable for this product."
}
```

### 1.2 `GET /api/v1/products/{product_id}/size-chart/revisions`
Returns an array of historical revision summaries with fingerprints and timestamps.

### 1.3 `GET /api/v1/products/{product_id}/variants`
Returns current variant availability:
```json
{
  "merchant_product_id": "d3b07384-d113-40f7-b08e-1616f7311ed1",
  "overall_status": "IN_STOCK",
  "variants": [
    {
      "variant_id": "var_m_navy",
      "size_label": "M",
      "colour_label": "Navy",
      "sku": "SKU-M-NAVY",
      "status": "IN_STOCK",
      "is_stale": false,
      "observed_at": "2026-11-25T10:00:00Z"
    }
  ],
  "last_checked_at": "2026-11-25T10:05:00Z"
}
```

### 1.4 `GET /api/v1/size-systems`
Returns registered sizing systems and supported labels.
