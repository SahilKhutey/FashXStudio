# FashXStudio — Analytics Event Taxonomy & Funnel Metrics

**Document ID:** `FASHX-ANL-001`  
**Version:** `1.0 — Execution Baseline`  
**Date:** `10 November 2026`  
**Scope:** `Phase 01.2 — Analytics & Telemetry Contract`  

---

## 1. Analytics Privacy & Security Rules

1. **Strict Pseudonymity:** User IDs are hashed (`usr_psd_9281a`). Raw email addresses, phone numbers, full names, and exact body measurements **must never** appear in telemetry payloads.
2. **Zero Image Telemetry:** Uploaded user photo URLs, image bytes, and face encodings are strictly excluded from analytics events.
3. **Multi-Tenant Isolation:** Analytics queries partition events by `merchant_id`. Cross-tenant data leakage is prevented via row-level database filters.
4. **Attribution Boundary:** An outbound redirect click represents **purchase intent**, not a confirmed commercial transaction.

---

## 2. Universal Event Envelope

Every client and server event conforms to this standard JSON envelope:

```json
{
  "event_id": "evt_9a8b7c6d-5e4f-3a2b-1c0d-e9f8a7b6c5d4",
  "event_name": "vto_job_completed",
  "event_version": 1,
  "occurred_at": "2026-11-10T08:00:22.450Z",
  "anonymous_session_id": "sess_81029384",
  "shopper_id": "usr_psd_481029",
  "merchant_id": "merch_d2c_001",
  "product_id": "prod_kurta_1082",
  "variant_id": "var_navy_m",
  "journey_id": "jny_feed_to_handoff_01",
  "properties": {
    "category": "ethnic_wear",
    "subcategory": "kurta",
    "vto_duration_ms": 14200,
    "quality_score": 0.92,
    "vto_attempt": 1
  }
}
```

---

## 3. Complete Instrumented Event Inventory

| Subsystem | Event Name | Core Properties | Business Significance |
| :--- | :--- | :--- | :--- |
| **Merchant** | `merchant_registration_started` | `source`, `country` | Funnel top: partner interest |
| **Merchant** | `merchant_registration_completed` | `merchant_id` | Partner acquisition milestone |
| **Merchant** | `merchant_verified` | `verification_method` | KYC / compliance milestone |
| **Merchant** | `merchant_permission_granted` | `scope`, `policy_version` | Legal clearance milestone |
| **Merchant** | `catalog_source_connected` | `source_type` (Shopify/Feed/CSV)| Technical integration established |
| **Merchant** | `catalog_import_started` | `source_id`, `import_job_id` | Data pipeline trigger |
| **Merchant** | `catalog_import_completed` | `total_count`, `valid_count`, `rejected`| Catalog ingestion health |
| **Merchant** | `catalog_product_approved` | `product_id`, `category` | Product curation milestone |
| **Merchant** | `catalog_product_published` | `product_id`, `vto_eligible` | Product available to shoppers |
| **Shopper** | `shopper_registration_completed` | `auth_provider` | Consumer acquisition |
| **Shopper** | `consent_decision_recorded` | `purpose`, `decision` (bool) | DPDP compliance record |
| **Shopper** | `profile_completed` | `completion_percentage` | Profile density metric |
| **Discovery** | `product_impression` | `product_id`, `placement` (feed/search)| Garment visibility |
| **Discovery** | `product_clicked` | `product_id`, `placement` | Garment interest |
| **Discovery** | `search_performed` | `category`, `result_count` | Search demand patterns |
| **Discovery** | `filter_applied` | `filter_type`, `filter_value` | Shopper preference refinement |
| **Product** | `product_detail_viewed` | `product_id`, `category`, `price` | High-intent consideration |
| **VTO** | `vto_cta_clicked` | `product_id`, `variant_id` | Try-on intent |
| **VTO** | `photo_upload_started` | `input_method` (camera/gallery) | Onboarding to VTO |
| **VTO** | `photo_validation_completed` | `passed` (bool), `failure_reason` | Photo quality telemetry |
| **VTO** | `vto_job_submitted` | `job_id`, `product_id`, `idempotency` | Compute workload initiated |
| **VTO** | `vto_job_started` | `job_id`, `worker_id` | Queue latency measurement |
| **VTO** | `vto_job_completed` | `job_id`, `duration_ms`, `quality` | Successful try-on delivered |
| **VTO** | `vto_job_failed` | `job_id`, `error_code`, `retryable` | ML / system failure tracking |
| **VTO** | `vto_retry_requested` | `previous_job_id`, `reason` | User retry behavior |
| **Wardrobe** | `look_saved` | `look_id`, `product_id`, `job_id` | High post-try-on engagement |
| **Wardrobe** | `look_deleted` | `look_id` | Closet curation |
| **Commerce** | `merchant_handoff_clicked` | `product_id`, `merchant_id`, `click_id`| Primary outbound conversion (intent)|
| **Commerce** | `merchant_handoff_opened` | `product_id`, `latency_ms` | Redirect delivery confirmation |
| **Feedback** | `vto_feedback_submitted` | `job_id`, `rating_stars`, `feedback_tag`| Real-world visual quality score |

---

## 4. Merchant Dashboard Funnel Metrics

The merchant analytics portal presents an actionable conversion funnel:

```
[1. Product Impressions] ➔ [2. Detail Views] ➔ [3. VTO Starts] ➔ [4. Completed VTOs] ➔ [5. Saved Looks] ➔ [6. Outbound Clicks]
```

### Funnel Metric Definitions

| Metric Name | Mathematical Definition | Strategic Interpretation |
| :--- | :--- | :--- |
| **Product Impressions** | Total count of `product_impression` events for merchant SKUs. | Overall catalog reach in feed and search. |
| **Product Detail Views** | Count of `product_detail_viewed` events. | Evaluation rate of specific merchant garments. |
| **VTO Initiation Rate** | $\frac{\text{vto\_cta\_clicked}}{\text{product\_detail\_viewed}} \times 100$ | Shopper desire to visualize the garment. |
| **VTO Completion Rate**| $\frac{\text{vto\_job\_completed}}{\text{vto\_job\_submitted}} \times 100$ | Technical reliability of AI generation pipeline. |
| **VTO Failure Rate** | $\frac{\text{vto\_job\_failed}}{\text{vto\_job\_submitted}} \times 100$ | Pipeline health (Target: $< 3\%$). |
| **Look Save Rate** | $\frac{\text{look\_saved}}{\text{vto\_job\_completed}} \times 100$ | Aesthetic satisfaction with generated result. |
| **Merchant Handoff Rate**| $\frac{\text{merchant\_handoff\_clicked}}{\text{product\_detail\_viewed}} \times 100$| Overall purchase intent generated by catalog listing. |
| **VTO Lift Multiplier** | $\frac{\text{Handoff Rate with VTO}}{\text{Handoff Rate without VTO}}$ | Core commercial value proposition for D2C brands. |
