> **Development log. Contains no real-world measurements or simulated evidence. Pre-pilot status maintained per AGENTS.md.**

# Dev Log: Phase 03.4 — Production Infrastructure and Backend Integration: Configure Object Storage

**Branch**: `recovery/rc13.1-governance-correction`
**Milestone Scope**: Phase 03 — Production Infrastructure and Backend Integration (Section 3.4: Configure Object Storage)
**Date**: November 14, 2026
**Status**: Completed & Verified Locally

---

## 1. Context & Architectural Decisions

Following the provisioning of PostgreSQL (Phase 03.2) and Redis / Valkey background workers (Phase 03.3), Phase 03.4 establishes the object storage tier for FashXStudio:

### Key Technical Decisions
1. **Managed Service**: **Amazon S3** in region **`ap-south-1` (Mumbai, India)** for low latency, data localization, and seamless IAM/KMS integration.
2. **Environment Separation**: 
   - Dedicated private buckets per environment: `fashx-dev-private-ACCOUNT_ID`, `fashx-staging-private-ACCOUNT_ID`, `fashx-prod-private-ACCOUNT_ID`.
   - Dedicated customer-managed KMS key per environment with 365-day rotation.
   - S3 Block Public Access enabled across all four vectors.
   - S3 BucketOwnerEnforced to disable ACLs.
   - Bucket policy `DenyInsecureTransport` enforcing TLS 1.2+ HTTPS.
3. **Prefix Partitioning**:
   - `products/{merchant_id}/{product_id}/{asset_id}.webp`: Authorized merchant catalog imagery.
   - `users/{user_id}/uploads/{asset_id}.jpg`: Private shopper uploads.
   - `tryon/{user_id}/{job_id}/result.webp`: Private generated VTO outputs.
   - `temporary/`: Staging buffers for client presigned POST uploads and batch ingest.
4. **Presigned URL Flow**:
   - 300-second (5 minute) short-lived presigned URLs.
   - Direct client upload via Presigned POST with strict `content-length-range` and MIME checks.
   - Two-step upload: Direct client upload to `temporary/uploads/` -> Backend verification and WebP normalization -> Promotion to final private key `users/{user_id}/uploads/`.
5. **Image Validation**:
   - Validation of actual image magic bytes (not trusting client-declared headers).
   - Strict size limits (10 MB shopper, 15 MB product/VTO).
   - Dimension limits (4096 × 4096).
   - Decompression bomb protection (20 megapixels maximum).
   - EXIF metadata stripping and WebP normalization.
6. **Retention and Erasure**:
   - Automatic S3 lifecycle rules for `temporary/` (1 day) and `tryon/` (30 days).
   - S3 Versioning disabled to ensure `DeleteObject` permanently erases objects immediately.
   - Outbox-driven user erasure workflow with verification probe (`object_exists`).

---

## 2. Technical Implementation Highlights

### A. Core Settings & Dependencies (`backend/fashx/core/settings.py` & `dependencies.py`)
- Added storage configuration fields:
  - `s3_kms_key_id`: Optional KMS master key ARN for SSE-KMS.
  - `s3_presigned_upload_ttl_seconds`: 300 seconds default.
  - `s3_presigned_download_ttl_seconds`: 300 seconds default.
  - `max_user_upload_bytes`: 10 MB default.
  - `max_product_image_bytes`: 15 MB default.
  - `max_vto_result_bytes`: 15 MB default.
  - `max_image_width`: 4096 default.
  - `max_image_height`: 4096 default.
  - `max_image_pixels`: 20,000,000 default.
- Wired `s3_kms_key_id` through `get_storage()` to `S3Storage`.

### B. Enhanced S3 Storage Adapter (`backend/fashx/infrastructure/storage/s3.py`)
- Added support for SSE-KMS encryption on object write (`put` and `copy`).
- Added `head()` for object metadata inspection.
- Added `copy()` for safe temporary-to-permanent promotion.
- Added `generate_presigned_post()` with KMS encryption headers and size conditions.
- Added static key validation `_validate_key()` preventing leading slashes and path traversal (`..`).

### C. Presigned URL Service (`backend/fashx/infrastructure/storage/presigned.py`)
- Standardized `UploadPolicy` dataclass with `USER_UPLOAD` and `PRODUCT_IMAGE_UPLOAD` presets.
- `create_upload_session()` generates unique server-side UUID keys under `temporary/` prefixes.
- `create_download_url()` provides validated presigned GET URLs with caller-specified TTL.

### D. Image Validation Service (`backend/fashx/infrastructure/storage/image_validation.py`)
- Rejects non-image binaries, SVG, HTML, and corrupted payloads.
- Validates magic bytes, checks for MIME spoofing, and enforces dimension limits.
- Automatically transposes image orientation per EXIF tags, strips all remaining EXIF metadata, and converts to WebP.

### E. Durable Deletion Service (`backend/fashx/infrastructure/storage/deletion.py`)
- `delete_object()`: Idempotent object deletion.
- `object_exists()`: Robust HeadObject probe distinguishing 404 / NoSuchKey from permission and service failures.
- `delete_prefix()`: Paginates and deletes batches of up to 1000 objects.

### F. Terraform & IAM Configurations (`infra/aws/`)
- `infra/aws/s3/main.tf`: Multi-environment buckets, KMS keys, public access blocks, ownership controls, lifecycle rules, and TLS enforcement.
- `infra/aws/iam/policies/`: 6 least-privilege IAM policy documents for Dev, Staging, and Prod VTO and Catalog task roles.

### G. Documentation Deliverables (`docs/infrastructure/`)
- Published 9 comprehensive specifications, runbooks, and security guides.
