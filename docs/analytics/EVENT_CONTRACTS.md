# FashXStudio — Universal Analytics Event Contracts & Specifications

**Document ID:** `FASHX-ANL-002`  
**Version:** `1.0 — Technical Baseline`  
**Date:** `10 November 2026`  
**Scope:** `Phase 01.5 — Technical Implementation & Event Engineering`  
**Parent Framework:** [KPI_DEFINITIONS.md](file:///c:/Users/ASUS/Documents/FashXStudio/docs/product/KPI_DEFINITIONS.md) & [ANALYTICS_EVENT_SPECIFICATION.md](file:///c:/Users/ASUS/Documents/FashXStudio/docs/product/analytics/ANALYTICS_EVENT_SPECIFICATION.md)

---

## 1. Technical Principles & Event Envelope Architecture

Every analytics and telemetry event in FashXStudio is formatted according to a universal, versioned JSON contract. Events are emitted transactionally upon confirmed backend state transitions and dispatched asynchronously to downstream storage.

### Universal Event Envelope Contract

```typescript
export interface UniversalEventEnvelope<T = Record<string, unknown>> {
  // Unique UUIDv4 event identifier (for deduplication)
  event_id: string;

  // Dot/Snake-cased event name matching the registered taxonomy
  event_name: string;

  // Monotonically increasing schema version
  event_version: number;

  // Microsecond-precision ISO 8601 UTC timestamp
  occurred_at: string;

  // Ephemeral client session tracking identifier (UUIDv4)
  session_id: string;

  // Cryptographically pseudonymous user reference (null for unauthenticated guests)
  shopper_id: string | null;

  // Merchant tenant UUID (null for platform-wide events)
  merchant_id: string | null;

  // Product and variant identifiers (where applicable)
  product_id: string | null;
  variant_id: string | null;

  // Correlation tracking across user journeys
  journey_id: string;
  trace_id: string;

  // Flag indicating automated tests, synthetic runs, or internal staff traffic
  is_internal: boolean;

  // Event-specific strongly typed properties
  properties: T;
}
```

---

## 2. Event Payload Contracts for Approved KPIs

### 2.1 Onboarding & Identity Contracts (KPI 1.4.1 & 1.4.2)

#### `registration_started`
- **Trigger:** User opens signup form or clicks social auth provider.
- **Payload Schema:**
  ```json
  {
    "acquisition_source": "organic_web | invite_link | merchant_embed",
    "referrer_url": "string (nullable)",
    "client_device": "android | ios | mobile_web | desktop_web",
    "app_version": "string"
  }
  ```

#### `registration_completed`
- **Trigger:** New account created and session token issued.
- **Payload Schema:**
  ```json
  {
    "auth_method": "password | magic_link | google | apple",
    "verification_time_seconds": "number",
    "country_code": "string (e.g. IN)"
  }
  ```

#### `profile_completed`
- **Trigger:** Minimum Viable Profile successfully stored in database.
- **Payload Schema:**
  ```json
  {
    "completion_score": "number (0.0 to 1.0)",
    "has_style_preferences": "boolean",
    "has_size_preferences": "boolean",
    "has_optional_measurements": "boolean",
    "dpdp_consent_granted": "boolean",
    "duration_seconds": "number"
  }
  ```

---

### 2.2 Discovery & Product Contracts (KPI 1.4.3 & 1.4.9)

#### `product_impression`
- **Trigger:** Product card rendered in visible viewport for $\ge 1.0$ second.
- **Payload Schema:**
  ```json
  {
    "surface": "home_feed | search_results | category_browse | similar_items",
    "grid_position": "integer",
    "category": "string",
    "price_inr": "number",
    "vto_eligible": "boolean",
    "impression_token": "string (UUID for deduplication)"
  }
  ```

#### `product_clicked`
- **Trigger:** Shopper taps a product card in any discovery view.
- **Payload Schema:**
  ```json
  {
    "surface": "home_feed | search_results | category_browse",
    "grid_position": "integer",
    "time_to_click_ms": "integer"
  }
  ```

#### `product_viewed`
- **Trigger:** Product Detail Page (PDP) loads all required metadata and images.
- **Payload Schema:**
  ```json
  {
    "merchant_id": "string (UUID)",
    "category": "mens_tshirt | mens_shirt | womens_top | kurta",
    "in_stock": "boolean",
    "vto_eligible": "boolean",
    "dwell_time_ms": "integer"
  }
  ```

---

### 2.3 Virtual Try-On Contracts (KPI 1.4.4, 1.4.5, 1.4.6, 1.4.7, 1.4.8)

#### `vto_started`
- **Trigger:** Valid try-on request accepted by API gateway and placed in queue.
- **Payload Schema:**
  ```json
  {
    "job_id": "string (UUID)",
    "input_method": "camera_capture | gallery_upload",
    "idempotency_key": "string",
    "category": "string",
    "garment_asset_id": "string (UUID)",
    "user_photo_asset_id": "string (UUID)"
  }
  ```

#### `vto_completed`
- **Trigger:** GPU inference succeeds, passes quality gate, and stores output in S3.
- **Payload Schema:**
  ```json
  {
    "job_id": "string (UUID)",
    "provider": "fashn",
    "model_version": "v1.5",
    "attempt_number": "integer (1 or 2)",
    "duration_queue_ms": "integer",
    "duration_preprocess_ms": "integer",
    "duration_provider_ms": "integer",
    "duration_postprocess_ms": "integer",
    "duration_total_ms": "integer",
    "provider_cost_inr": "number",
    "automated_quality_score": "number (0.0 to 1.0)"
  }
  ```

#### `vto_failed`
- **Trigger:** Job enters terminal failure state after allowed retries or timeout.
- **Payload Schema:**
  ```json
  {
    "job_id": "string (UUID)",
    "provider": "fashn",
    "attempt_number": "integer",
    "failure_category": "input_rejection | provider_timeout | quality_check_failed | storage_error",
    "error_code": "string",
    "is_retryable": "boolean",
    "duration_elapsed_ms": "integer"
  }
  ```

#### `vto_feedback_submitted`
- **Trigger:** Shopper or reviewer submits quality ratings on result.
- **Payload Schema:**
  ```json
  {
    "job_id": "string (UUID)",
    "reviewer_type": "shopper | internal_reviewer",
    "visual_realism_score": "integer (1 to 5)",
    "garment_preservation_score": "integer (1 to 5)",
    "issue_tags": ["string (e.g. skin_tone_warp, blur, color_mismatch)"]
  }
  ```

---

### 2.4 Digital Wardrobe & Commerce Contracts (KPI 1.4.10, 1.4.11, 1.4.14)

#### `look_saved`
- **Trigger:** Shopper saves try-on result to personal wardrobe.
- **Payload Schema:**
  ```json
  {
    "look_id": "string (UUID)",
    "job_id": "string (UUID)",
    "variant_id": "string (UUID)",
    "price_snapshot_inr": "number",
    "tags": ["string"]
  }
  ```

#### `merchant_outbound_clicked`
- **Trigger:** Shopper taps "Buy at Merchant" and server initiates verified redirect.
- **Payload Schema:**
  ```json
  {
    "click_id": "string (UUID)",
    "merchant_id": "string (UUID)",
    "product_id": "string (UUID)",
    "destination_domain": "string",
    "prior_vto_completed": "boolean",
    "time_since_vto_ms": "integer (nullable)"
  }
  ```
