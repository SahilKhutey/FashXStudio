# FashXStudio — Object Retention & Lifecycle Policy (Phase 03.4)

## 1. Overview
Object retention is managed via a combination of automated Amazon S3 lifecycle rules and application-level erasure workflows.

---

## 2. Retention Matrix

| Data Classification | Storage Prefix | Retention Period | Deletion Mechanism |
| :--- | :--- | :--- | :--- |
| **Temporary Uploads** | `temporary/uploads/` | 1 day maximum | S3 Lifecycle Rule + Immediate post-validation cleanup |
| **Temporary VTO Inputs** | `temporary/tryon/` | 1 day maximum | S3 Lifecycle Rule + Post-inference worker cleanup |
| **Temporary Catalog Feeds** | `temporary/ingest/` | 1 day maximum | S3 Lifecycle Rule + Post-ingest worker cleanup |
| **VTO Render Results** | `tryon/` | 30 days default | S3 Lifecycle Rule + On-demand user profile erasure |
| **User Uploads (Originals)** | `users/` | User consent duration | Application erasure outbox workflow |
| **Product Imagery** | `products/` | Merchant license duration| Merchant source removal or rights revocation |

---

## 3. Automated S3 Lifecycle Configuration
Codified in `infra/aws/s3/main.tf`:
- `expire-temporary-objects`: Prefix `temporary/`, expires after 1 day. Incomplete multipart uploads aborted after 1 day.
- `expire-old-vto-results`: Prefix `tryon/`, expires after 30 days. Incomplete multipart uploads aborted after 1 day.
- `users/` and `products/`: No automated expiration. Controlled strictly by user consent and business contracts.

---

## 4. Versioning Policy
- **Status**: Disabled (`versioning = "Suspended"`).
- **Rationale**: For user data erasure compliance, ordinary `DeleteObject` calls must permanently remove the object immediately rather than appending an S3 delete marker with retained historical versions.
