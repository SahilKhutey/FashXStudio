# FashXStudio — S3 Security & Boundary Testing Guide (Phase 03.4)

## 1. Overview
Object storage security must be verified across three distinct isolation boundaries:
1. **Public Boundary**: Anonymous unauthenticated requests to bucket endpoints must be rejected (Block Public Access + TLS policy).
2. **Environment Boundary**: Development or staging credentials must be denied access to production buckets.
3. **Application Boundary**: Authenticated users must not be able to download, upload to, or delete another user's private media.

---

## 2. Test Execution Procedures

### 2.1 Anonymous Direct Object Access
Test that requesting any object without AWS signature credentials returns HTTP 403 AccessDenied:

```bash
curl -i "https://fashx-prod-private-ACCOUNT_ID.s3.ap-south-1.amazonaws.com/users/test/file.webp"
```
Expected output:
```text
HTTP/1.1 403 Forbidden
<Error><Code>AccessDenied</Code><Message>Access Denied</Message></Error>
```

### 2.2 Cross-Environment Denial
From a container running with the development ECS task role, attempt to fetch an object from the staging bucket:

```bash
aws s3api get-object \
  --bucket fashx-staging-private-ACCOUNT_ID \
  --key products/test/product.webp \
  /tmp/test.webp
```
Expected output:
```text
An error occurred (AccessDenied) when calling the GetObject operation: Access Denied
```

### 2.3 Cross-User Authorization Denial
Simulate User B attempting to request a download URL for User A's photo:
- Verified by automated unit test `test_cross_user_media_access_rejected_by_application_policy` in `tests/integration/storage/test_s3_access_control.py`.
- The application layer throws `PermissionError` or returns HTTP 404 / 403 before calling `create_download_url()`.

### 2.4 Presigned URL Expiration
Verify that a presigned GET URL ceases to function once `expires_in` seconds have elapsed:
- Tested in `tests/integration/storage/test_presigned_expiration.py`.
- S3 returns HTTP 403 `Request has expired`.

---

## 3. Automated Test Suite Commands
Execute the storage test suite locally:

```bash
python -m pytest tests/infrastructure/storage/ tests/integration/storage/ -v
```
All 41 collected tests pass (or skip conditionally when live AWS integration flag is not set).
