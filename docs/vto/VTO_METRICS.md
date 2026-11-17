# FashXStudio — Virtual Try-On Technical Metrics & Lifecycle Architecture

**Document ID:** `FASHX-VTO-001`  
**Version:** `1.0 — Execution Baseline`  
**Date:** `10 November 2026`  
**Scope:** `Phase 01.4 — VTO Technical Measurement Specification`  

---

## 1. VTO Job Success vs. Attempt Accounting

To prevent provider instability from being obscured by excessive retries, FashXStudio tracks both:
- **First-Attempt Success Rate:** Percentage of jobs that succeed on attempt #1 without retry.
- **Eventual Job Success Rate:** Percentage of logical jobs that reach `completed` within the permitted maximum retry ceiling (Max: 1 automated retry).

$$\text{First-Attempt Success Rate} = \frac{\text{Jobs completed on attempt 1}}{\text{Total accepted jobs}} \times 100$$

$$\text{Eventual Job Success Rate} = \frac{\text{Total jobs reaching terminal state } \texttt{completed}}{\text{Total accepted jobs}} \times 100$$

*Quality Rule:* A job requiring more than 1 retry is classified as a pipeline defect.

---

## 2. Latency Stage Decomposition

Every VTO job records microsecond-precision timestamps at each state transition:

$$T_{\text{total}} = T_{\text{queue}} + T_{\text{preprocess}} + T_{\text{provider}} + T_{\text{postprocess}} + T_{\text{storage}}$$

```
[Job Accepted] 
      │ ──► T_queue (Waiting in Redis queue for available worker)
[Processing Started]
      │ ──► T_preprocess (Image decoding, pose validation, mask generation)
[Dispatched to Provider]
      │ ──► T_provider (FASHN.ai hosted diffusion inference)
[Synthesis Received]
      │ ──► T_postprocess (Artifact screening, face alignment check)
[Uploading Result]
      │ ──► T_storage (S3 multipart upload and presigned URL generation)
[Job Completed]
```

### Stage Latency Budgets (P95 Targets)
- $T_{\text{queue}}$: $< 3.0$ seconds.
- $T_{\text{preprocess}}$: $< 4.0$ seconds.
- $T_{\text{provider}}$: $< 28.0$ seconds.
- $T_{\text{postprocess}}$: $< 5.0$ seconds.
- $T_{\text{storage}}$: $< 3.0$ seconds.
- **Total P95 Budget:** $< 45.0$ seconds.

---

## 3. Two-Tier Image Failure Taxonomy

Failures are bifurcated to prevent user-upload errors from polluting AI provider SLA calculations:

### Tier 1: Input Rejection Rate (User Photo Issues)
$$\text{Input Rejection Rate} = \frac{\text{Uploads failing stage 1–7 validation}}{\text{Total uploaded image assets}} \times 100$$
- `REJECT_FORMAT_INVALID`: Unsupported MIME type or corrupt header.
- `REJECT_RESOLUTION_LOW`: Dimensions below $768 \times 1024$ px.
- `REJECT_MULTI_PERSON`: Multiple human bodies detected.
- `REJECT_SEVERE_OCCLUSION`: Hands/objects blocking chest or torso.
- `REJECT_EXTREME_POSE`: Subject lying down, seated, or twisted $\ge 45^\circ$.

### Tier 2: Pipeline Image Failure Rate (System / Model Issues)
$$\text{Pipeline Failure Rate} = \frac{\text{Accepted jobs terminated in } \texttt{failed}}{\text{Total accepted jobs}} \times 100$$
- `ERR_GARMENT_SEGMENTATION`: Background removal worker failed on merchant asset.
- `ERR_PROVIDER_TIMEOUT`: FASHN API did not return output within 30s.
- `ERR_PROVIDER_REJECTED`: FASHN API returned 4xx/5xx status.
- `ERR_ARTIFACT_DETECTED`: Postprocessing detected blank image, severe warping, or color inversion.
- `ERR_STORAGE_WRITE`: Failed to persist generated output to S3 bucket.

---

## 4. Durable VTO Job Database Schema

In addition to ephemeral Redis state and analytics logs, the PostgreSQL database persists an authoritative `vto_jobs` table:

```sql
CREATE TABLE vto_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    merchant_id UUID NOT NULL REFERENCES merchants(id),
    product_id UUID NOT NULL REFERENCES products(id),
    variant_id UUID NOT NULL REFERENCES product_variants(id),
    
    -- Status & Lifecycle State
    status VARCHAR(32) NOT NULL DEFAULT 'created',
    attempt_count INT NOT NULL DEFAULT 1,
    idempotency_key VARCHAR(128) UNIQUE NOT NULL,
    
    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    accepted_at TIMESTAMPTZ,
    queued_at TIMESTAMPTZ,
    processing_started_at TIMESTAMPTZ,
    processing_completed_at TIMESTAMPTZ,
    result_stored_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    failed_at TIMESTAMPTZ,
    
    -- Stage Latency Durations (Milliseconds)
    duration_queue_ms INT,
    duration_preprocess_ms INT,
    duration_provider_ms INT,
    duration_postprocess_ms INT,
    duration_total_ms INT,
    
    -- Provider & Model Tracking
    provider VARCHAR(32) NOT NULL DEFAULT 'fashn',
    model_version VARCHAR(32) NOT NULL DEFAULT 'v1.5',
    provider_job_id VARCHAR(128),
    provider_cost NUMERIC(8, 4),
    currency VARCHAR(8) DEFAULT 'INR',
    
    -- Asset References
    shopper_asset_id UUID NOT NULL,
    garment_asset_id UUID NOT NULL,
    result_asset_key VARCHAR(512),
    result_expires_at TIMESTAMPTZ,
    
    -- Failure Diagnostics
    failure_category VARCHAR(64),
    error_code VARCHAR(64),
    error_message_safe TEXT,
    
    -- Governance Traces
    consent_id UUID NOT NULL,
    permission_id UUID NOT NULL
);

CREATE INDEX idx_vto_jobs_user_status ON vto_jobs(user_id, status);
CREATE INDEX idx_vto_jobs_merchant_created ON vto_jobs(merchant_id, created_at);
CREATE INDEX idx_vto_jobs_idempotency ON vto_jobs(idempotency_key);
```
