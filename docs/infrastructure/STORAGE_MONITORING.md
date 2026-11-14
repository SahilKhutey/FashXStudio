# Object Storage Monitoring Specification

## 1. Overview

FashXStudio stores all product media, user-uploaded model images, and rendered Virtual Try-On outputs in private Amazon S3 buckets segregated by environment:
- `fashx-dev-private-<ACCOUNT_ID>`
- `fashx-staging-private-<ACCOUNT_ID>`
- `fashx-prod-private-<ACCOUNT_ID>`

Storage telemetry is instrumented directly within the S3 adapter (`backend/fashx/infrastructure/storage/s3.py`) using AWS CloudWatch Embedded Metric Format (EMF) directed to stdout.

## 2. Emitted Storage Metrics (`FashX/Storage`)

Every upload, download, and deletion is timed and counted:

| Metric Name | Type | Unit | Description |
| :--- | :--- | :--- | :--- |
| `StorageUploadCount` | Counter | Count | Total successful object uploads to S3. |
| `StorageBytesUploaded` | Counter | Bytes | Total bytes written to S3 storage. |
| `StorageDownloadCount` | Counter | Count | Total successful object retrievals from S3. |
| `StorageDeleteCount` | Counter | Count | Total successful object deletions from S3. |
| `StorageOperationLatency` | Timer | Milliseconds | Wall-clock latency for S3 API calls (`put`, `get`, `delete`). |
| `StorageUploadError` | Counter | Count | Failures encountered during upload operations. |
| `StorageDownloadError` | Counter | Count | Failures encountered during download operations. |
| `StorageDeleteError` | Counter | Count | Failures encountered during delete operations. |

## 3. Allowed Dimensions & Cardinality Protection

To prevent high-cardinality custom metric generation, object keys and user UUIDs are strictly stripped from dimensions.

### Allowed Dimensions
- `Environment`: `dev`, `staging`, `prod`
- `Operation`: `put`, `get`, `delete`
- `Category`: Logical storage prefix (`products`, `users`, `tryon`, `temp`)

### Prohibited Dimensions
Object keys (e.g. `users/usr_8f1a/selfie.jpg`), presigned URLs, and customer IDs must never be used as metric dimensions. The adapter automatically extracts the top-level prefix (`category = key.split('/')[0]`) as the safe dimension.

## 4. Erasure Compliance & Data Privacy Telemetry

In accordance with data privacy regulations (GDPR Article 17 and Digital Personal Data Protection Act):
- When a user deletes an uploaded photo or requests profile erasure, all associated objects under `users/{user_id}/` and `tryon/{job_id}/` must be purged.
- Any non-zero count of `StorageDeleteError` raises an immediate P2 alert to ensure no lingering customer imagery remains unexpunged.

## 5. Storage Latency & Error Alarms

1. **`S3-Storage-Errors-Production`**:
   - Condition: `Sum(StorageUploadError + StorageDownloadError + StorageDeleteError) > 5` within a 5-minute window.
   - Action: P1 alert to `fashx-alerts-prod`.
2. **`S3-Latency-High-Production`**:
   - Condition: `p95(StorageOperationLatency) > 1000 ms` for 5 minutes.
   - Action: P2 alert to inspect AWS S3 regional latency or VPC endpoint saturation.

## 6. Verification & Automated Testing

Storage telemetry is verified by unit tests in `tests/observability/test_storage_metrics.py`:
- `test_storage_put_emits_metrics`: Validates `StorageUploadCount`, `StorageBytesUploaded`, and `StorageOperationLatency`.
- `test_storage_delete_emits_metrics`: Confirms `StorageDeleteCount` and category dimension extraction.
- `test_storage_error_metrics_emitted`: Asserts error counters increment on mock S3 client exceptions.
