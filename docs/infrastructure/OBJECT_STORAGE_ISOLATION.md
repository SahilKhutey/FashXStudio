# Object Storage Isolation & Security Specification

## 1. Bucket Architecture & Separation

In strict compliance with **ADR-0005: Private Object Storage with Presigned URLs**, all media assets, garment source images, shopper try-on uploads, and generated inference outputs are stored in dedicated private object storage buckets.

Each environment operates an isolated bucket with non-overlapping access boundaries:

| Environment | Bucket Identifier | Access Restriction | Encryption |
| :--- | :--- | :--- | :--- |
| **Development** | `fashx-dev-media-private` | Development ECS Task Role only | AWS SSE-S3 |
| **Staging** | `fashx-staging-media-private` | Staging ECS Task Role only | AWS SSE-S3 / SSE-KMS |
| **Production** | `fashx-prod-media-private` | Production ECS Task Role only | AWS SSE-KMS (Customer Managed Key) |

```mermaid
flowchart TD
    subgraph S3Bucket ["S3: fashx-prod-media-private (100% Private, BlockPublicAccess=True)"]
        Garments["catalog/garments/*\n(Permanent catalog assets)"]
        Uploads["shopper-uploads/*\n(Ephemeral user input, TTL 7d)"]
        Outputs["tryon-outputs/*\n(Generated try-on imagery, TTL 30d)"]
    end

    ShopperClient["Mobile / Web Client"]
    FastAPIApp["FashX Backend (ECS Task)"]

    ShopperClient -->|1. Request Presigned URL| FastAPIApp
    FastAPIApp -->|2. Generate URL (TTL 300s) via IAM Role| S3Bucket
    FastAPIApp -->|3. Return Presigned URL| ShopperClient
    ShopperClient -->|4. Direct PUT / GET with Presigned URL| S3Bucket
```

---

## 2. Public Access Block Invariant

Every FashXStudio storage bucket enforces AWS S3 Public Access Block at both the account and bucket levels:

```json
{
  "BlockPublicAcls": true,
  "IgnorePublicAcls": true,
  "BlockPublicPolicy": true,
  "RestrictPublicBuckets": true
}
```

Direct anonymous HTTP access to any object or bucket is completely impossible. Any bucket policy attempting to allow `Principal: "*"` will fail deployment validation.

---

## 3. Presigned URL Pattern & Expiry Rules

To protect shopper privacy and eliminate intermediate image buffering through application servers:

1. **Client Direct Upload**: When a shopper uploads an outfit or body image for virtual try-on, the application issues a presigned `PUT` URL.
2. **Short Time-to-Live (TTL)**: The maximum expiry for presigned upload and download URLs is **300 seconds (5 minutes)**.
3. **Restricted Operations**: Presigned URLs are strictly scoped to the exact key path, with content-type and content-length restrictions enforced during signature creation.

---

## 4. Authentication Mechanism (`S3_USE_IAM_ROLE`)

Long-lived AWS access keys (`S3_ACCESS_KEY_ID`, `S3_SECRET_ACCESS_KEY`) represent a severe credential leakage vector and are forbidden in hosted environments:

- In Development and Local testing, mock keys or explicit sandbox credentials may be supplied.
- In Staging and Production, `S3_USE_IAM_ROLE=true` is mandatory. The application utilizes the AWS default credential provider chain (OIDC / IAM Roles for ECS Tasks / IRSA), obtaining short-lived, automatically rotated STS credentials.

---

## 5. Lifecycle Management and Retention Policies

To optimize storage costs and satisfy biometric data privacy policies:

| Object Prefix | Retention Window | Storage Class Transition | Deletion Action |
| :--- | :--- | :--- | :--- |
| `shopper-uploads/` | 7 days | Standard | Permanent Expiration |
| `tryon-outputs/` | 30 days | Standard -> Infrequent Access (at 14d) | Permanent Expiration |
| `catalog/garments/` | Indefinite | Standard -> Intelligent-Tiering (at 30d) | Retained indefinitely |
| `backups/exports/` | 90 days | Glacier Instant Retrieval (at 30d) | Permanent Expiration |
