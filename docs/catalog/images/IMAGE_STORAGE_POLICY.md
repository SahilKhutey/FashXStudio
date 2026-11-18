# Image Storage Policy

## 1. Storage Architecture & Privacy Boundary

All product images and derivatives are persisted exclusively into private Amazon S3 buckets (or encrypted local storage in development). Public bucket access is permanently disabled.

---

## 2. Standardized Object Key Layout

```
catalog/
  {environment}/
    sources/
      {source_id}/
        originals/
          {asset_id}/{original_sha256}.{ext}
        display/
          {asset_id}/{version}_{variant}.webp
        vto/
          {asset_id}/{version}.png
```

### Key Formatting Rules
1. **No External Filenames**: Merchant-supplied file paths and names (`image.jpg`, `photo1.png`) are never used as S3 object keys.
2. **KMS Encryption**: All objects are server-side encrypted using the environment-specific AWS KMS CMK (`aws:kms`).
3. **MIME Types**: Stored with explicit `ContentType` headers matching verified image payloads.
4. **Short-Lived Signed URLs**: Access is granted strictly via expiring pre-signed URLs (default 900 seconds). Signed URLs are never logged or stored in plain text.

---

## 3. Atomic Compensation Cleanup

If a database transaction fails during asset creation or transformation indexing, the pipeline executes compensation cleanup, deleting the uncommitted S3 objects to prevent storage leaks.
