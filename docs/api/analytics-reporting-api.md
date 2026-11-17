# FashXStudio — Analytics Reporting & Dashboard API Specifications

**Document ID:** `FASHX-API-002`  
**Version:** `1.0 — Technical Baseline`  
**Date:** `10 November 2026`  
**Scope:** `Phase 01.5 — REST API Endpoints for KPI Reporting & Exports`  

---

## 1. Internal Founder / Admin KPI Summary API

- **Endpoint:** `GET /api/v1/admin/kpis/summary`
- **Authorization:** `Bearer <token>` with `ROLE_ADMIN`
- **Query Parameters:**
  - `window_days`: Integer (`1`, `7`, `30`, default `7`)
  - `include_internal`: Boolean (default `false`)

### Response Payload (`HTTP 200 OK`)
```json
{
  "data": {
    "reporting_window": {
      "start_at": "2026-11-03T00:00:00Z",
      "end_at": "2026-11-10T00:00:00Z"
    },
    "kpis": {
      "registration_completion_rate": 0.742,
      "profile_completion_rate": 0.685,
      "discovery_success_rate": 0.321,
      "vto_job_success_rate": 0.918,
      "vto_p95_latency_seconds": 38.4,
      "visual_realism_avg": 4.12,
      "garment_preservation_avg": 3.95,
      "pipeline_image_failure_rate": 0.038,
      "product_ctr": 0.124,
      "saved_look_rate": 0.231,
      "d7_retention_rate": 0.182,
      "active_merchants_count": 1,
      "direct_cost_per_vto_inr": 9.40
    },
    "decision_gate_status": {
      "G1_onboarding": "PASS",
      "G2_discovery": "PASS",
      "G3_vto_reliability": "PASS",
      "G4_vto_latency": "PASS",
      "G5_visual_quality": "PASS",
      "G6_engagement": "PASS",
      "G7_merchant": "PASS",
      "G8_economics": "PASS"
    }
  },
  "meta": {
    "request_id": "req_8192a01",
    "computed_at": "2026-11-10T08:00:00Z"
  }
}
```

---

## 2. Merchant Partner Analytics API

- **Endpoint:** `GET /api/v1/merchants/{id}/analytics`
- **Authorization:** `Bearer <token>` with `ROLE_MERCHANT_ADMIN` (Tenant ID must match path ID)
- **Query Parameters:**
  - `start_date`: ISO Date (`YYYY-MM-DD`)
  - `end_date`: ISO Date (`YYYY-MM-DD`)

### Response Payload (`HTTP 200 OK`)
```json
{
  "data": {
    "merchant_id": "merch_d2c_001",
    "summary": {
      "total_impressions": 1420,
      "product_detail_views": 380,
      "vto_initiations": 112,
      "vto_completed": 104,
      "looks_saved": 28,
      "merchant_handoff_clicks": 42,
      "vto_completion_rate": 0.928,
      "vto_to_handoff_rate": 0.404
    },
    "daily_breakdown": [
      {
        "date": "2026-11-09",
        "impressions": 310,
        "detail_views": 85,
        "vto_completed": 24,
        "handoff_clicks": 10
      }
    ]
  },
  "meta": {
    "request_id": "req_4901b02",
    "timestamp": "2026-11-10T08:00:00Z"
  }
}
```

---

## 3. Asynchronous Analytics CSV Export API

- **Endpoint:** `POST /api/v1/merchants/{id}/analytics/exports`
- **Payload:**
  ```json
  {
    "format": "csv",
    "date_range": {
      "start_date": "2026-11-01",
      "end_date": "2026-11-10"
    },
    "metrics": ["impressions", "vto_completed", "saved_looks", "handoff_clicks"]
  }
  ```
- **Response (`HTTP 202 Accepted`):**
  ```json
  {
    "data": {
      "export_job_id": "job_exp_9281",
      "status": "processing",
      "download_url": null
    }
  }
  ```
