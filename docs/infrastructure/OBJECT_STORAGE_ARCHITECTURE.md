# FashXStudio Object Storage Architecture (Phase 03.4)

## 1. Storage Provider
- **Provider**: Amazon S3
- **Primary Region**: AWS `ap-south-1` (Mumbai, India)

## 2. Environment Isolation
Each environment runs one completely private bucket with dedicated KMS keys, access policies, and network boundaries:
- **Development**: `fashx-dev-private-ACCOUNT_ID`
- **Staging**: `fashx-staging-private-ACCOUNT_ID`
- **Production**: `fashx-prod-private-ACCOUNT_ID`

Cross-environment bucket access is strictly denied at both the IAM and bucket-policy levels. Development or staging credentials cannot read or write to production buckets.

## 3. Storage Prefixes and Conventions
Within each bucket, logical data categories are partitioned by opaque prefixes:
- `products/{merchant_id}/{product_id}/{asset_id}.webp`: Merchant-cleared catalog imagery.
- `users/{user_id}/uploads/{asset_id}.jpg`: Sensitive shopper profile uploads.
- `tryon/{user_id}/{job_id}/result.webp`: Private generated virtual try-on outputs.
- `temporary/uploads/`: Staging buffer for client presigned POST uploads.
- `temporary/tryon/`: Ephemeral intermediate artifacts generated during VTO inference.
- `temporary/ingest/`: Ephemeral product catalog batch feed downloads.

## 4. Security & Encryption Standards
- **S3 Block Public Access**: All four controls (`block_public_acls`, `ignore_public_acls`, `block_public_policy`, `restrict_public_buckets`) are enabled.
- **Bucket Ownership Controls**: Set to `BucketOwnerEnforced`. S3 ACLs are completely disabled.
- **Encryption at Rest**: Mandatory AWS SSE-KMS with dedicated customer-managed keys per environment and automatic 365-day key rotation enabled (`alias/fashx-${env}-s3`).
- **Encryption in Transit**: Enforced via bucket policy `DenyInsecureTransport`, rejecting any request not utilizing HTTPS (TLS 1.2+).
- **Authentication**: Dedicated ECS IAM task roles. Static AWS access keys are prohibited in hosted environments.
- **Access Delivery**: Short-lived presigned URLs (default 300 seconds TTL) generated only after PostgreSQL ownership verification.

## 5. Image Validation & Ingestion Controls
- **Accepted Formats**: JPEG, PNG, WebP only. SVG, HTML, HEIC, and arbitrary binaries are rejected.
- **Payload Limits**: 10 MB maximum for shopper uploads; 15 MB maximum for merchant product imagery and VTO outputs.
- **Dimensions**: Maximum 4096 × 4096 pixels; maximum 20 megapixels total pixel count (decompression bomb protection).
- **Normalization**: Server-side EXIF metadata stripping and automated conversion to WebP format.

## 6. Retention and Lifecycle
- `temporary/`: Expired automatically after 1 day; incomplete multipart uploads aborted after 1 day.
- `tryon/`: Expired after 30 days by default (or erased immediately upon user profile deletion).
- `users/`: Retained strictly per user consent and profile lifecycle; purged immediately on account erasure.
- `products/`: Retained while merchant license and catalog source rights remain valid.

## 7. Deletion & User Erasure
User media deletion is durable, verified, and idempotent:
1. Intent recorded in PostgreSQL outbox.
2. Original, derived, and temporary objects deleted via S3 API.
3. Verification probe confirms HTTP 404 / NoSuchKey before marking erasure complete.
