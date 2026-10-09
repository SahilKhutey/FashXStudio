# Phase 4: Object Storage Real Bucket Validation Check

_Date: 2026-10-09 · Target: Cloudflare R2 / AWS S3 Production Hardening_

This document specifies the validation procedure and operational verification steps for real Cloudflare R2 / AWS S3 object storage buckets in production environments, adhering to Gate G4 and Rule I06.

---

## 1. Bucket Security Posture Requirements

1. **Private Access by Default**:
   - AWS S3: "Block all public access" must be enabled (all 4 settings: `BlockPublicAcls`, `IgnorePublicAcls`, `BlockPublicPolicy`, `RestrictPublicBuckets` set to `True`).
   - Cloudflare R2: Public access must be disabled; no custom domains mapped directly to the bucket.
2. **Access Control**:
   - Access is restricted exclusively to the backend IAM role / API tokens with least privilege (`PutObject`, `GetObject`, `DeleteObject`, `ListBucket` scoped strictly to `u/*` and `catalog/*`).
3. **CORS Policy** (if direct mobile client downloads occur via presigned URLs):
   ```json
   [
     {
       "AllowedHeaders": ["*"],
       "AllowedMethods": ["GET"],
       "AllowedOrigins": ["https://app.fashx.studio", "fashx://*"],
       "ExposeHeaders": ["ETag"],
       "MaxAgeSeconds": 3600
     }
   ]
   ```
4. **Lifecycle & Retention**:
   - Optional lifecycle rule for temporary try-on artifacts or orphan scratch files: auto-delete objects under `scratch/` after 24 hours.

---

## 2. Environment Configuration

In production, set the following environment variables (fail-fast validated in `fashx.core.settings.Settings`):

```bash
ENV=prod
STORAGE_BACKEND=s3
S3_REGION=auto                   # or eu-west-1 / us-east-1
S3_BUCKET=fashx-production-media
S3_ENDPOINT_URL=https://<account-id>.r2.cloudflarestorage.com
S3_ACCESS_KEY_ID=<secret-access-key-id>
S3_SECRET_ACCESS_KEY=<secret-access-key>
SIGNED_URL_TTL_S=300
```

> **Warning:** If `ENV=prod` and `STORAGE_BACKEND` is set to `local` or credentials are unset, the application refuses to start.

---

## 3. Real Bucket End-to-End Test Procedure

A manual validation run with real credentials before production rollout must execute the following sequence:

1. **Upload Validation**:
   - Upload sample test image with key `u/00000000-0000-0000-0000-000000000001/photos/sample.jpg`.
   - Verify Content-Type is set to `image/jpeg`.
2. **Direct Public Download Attempt (Security Check)**:
   - Attempt anonymous curl against the raw bucket URL:
     `curl -I https://fashx-production-media.s3.amazonaws.com/u/00000000-0000-0000-0000-000000000001/photos/sample.jpg`
   - Must return HTTP 403 Forbidden.
3. **Signed Capability URL Validation**:
   - Call `storage.signed_get_url(key, ttl_s=300)`.
   - Download the file using the presigned URL with curl.
   - Must return HTTP 200 OK and valid image bytes.
4. **Expiration Check**:
   - Generate signed URL with `ttl_s=1`.
   - Wait 2 seconds.
   - Fetch the URL: must return HTTP 403 Access Denied / Request has expired.
5. **Prefix Erasure Check**:
   - Call `storage.delete_prefix("u/00000000-0000-0000-0000-000000000001/")`.
   - Verify `storage.exists(key)` returns `False`.
   - Verify bucket contains zero residual objects for that user prefix.

---

## 4. Contract and Integration Test Status

All 8 contract test cases in `tests/contracts/test_storage.py` and erasure integration tests in `tests/integration/test_erasure.py` have passed:
- `test_put_get_exists_delete[s3]` ✅ (tested via Moto against real S3 API semantics)
- `test_delete_prefix_removes_all_and_only_prefix[s3]` ✅
- `test_list_prefix_paginates_over_1000[s3]` ✅
- `test_signed_url_is_generated_and_not_stored[s3]` ✅
- `test_erasure_pipeline_local_storage` ✅
- `test_every_model_table_is_classified` ✅
