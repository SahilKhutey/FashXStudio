# Media Storage Key Policy

## 1. Core Principles
1. **Zero Client Path Control**: The storage key used in Amazon S3 is generated exclusively by the backend using UUIDv4 identifiers. Client-supplied filenames, user handles, or form parameters are never incorporated into storage paths.
2. **Path Traversal Prevention**: Because the storage key contains only server-controlled UUIDs and fixed directory segments, directory traversal (`../`) and bucket escaping attacks are structurally impossible.
3. **Information Disclosure Prevention**: User IDs are internal UUIDs, not usernames, email addresses, or Cognito IDs, preventing identity enumeration through key logging or inspection.

---

## 2. Storage Key Formats

### 2.1 Quarantine Key Schema
Used for temporary, unverified uploads directly from the mobile client:
```text
temporary/uploads/{environment}/{user_id}/{upload_id}/original
```
- `{environment}`: `dev`, `staging`, or `prod`.
- `{user_id}`: The internal UUID of the user account.
- `{upload_id}`: A unique UUIDv4 generated for the specific upload intent.
- `original`: Fixed filename segment.

### 2.2 Validated Media Key Schema
Used for verified, normalized, and stripped image assets:
```text
users/{user_id}/images/{image_id}/original.webp
```
- `{user_id}`: The internal UUID of the user account.
- `{image_id}`: The permanent UUIDv4 assigned to the validated media asset.
- `original.webp`: Fixed filename indicating normalized WebP raster format.

---

## 3. S3 Bucket Security Policies
- **Block Public Access**: S3 Block Public Access is set to `True` for all four settings (BlockPublicAcls, IgnorePublicAcls, BlockPublicPolicy, RestrictPublicBuckets).
- **Server-Side Encryption**: Encrypted at rest using AWS KMS (`aws:kms`) or Amazon S3 managed keys (`AES256`).
- **Transport Security**: S3 bucket policies mandate `aws:SecureTransport: true` (enforcing TLS 1.3/1.2).
- **Quarantine Lifecycle**: S3 lifecycle configuration automatically purges objects under `temporary/uploads/` after 24 hours in the event of worker or network cancellation.
