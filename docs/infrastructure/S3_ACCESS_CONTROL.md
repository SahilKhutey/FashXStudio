# FashXStudio — S3 Access Control & IAM Matrix (Phase 03.4)

## 1. Core Principles
1. **No Public S3 Access**: No public bucket policies, no public objects, no public ACLs.
2. **ECS Task Roles Only**: All application services authenticate using IAM task roles attached to ECS tasks. Static credentials (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`) are prohibited in hosted environments.
3. **Environment Isolation**:
   - Dev roles access Dev buckets only.
   - Staging roles access Staging buckets only.
   - Production roles access Production buckets only.
   - Cross-environment IAM requests are rejected.
4. **Least-Privilege Prefix Grant**: Services are granted access only to the explicit S3 prefixes required for their domain.
5. **Application-Level Ownership Authorization**: Possession of an object key does not grant download access. The FastAPI backend validates user ownership or merchant rights in PostgreSQL before generating a signed URL.

---

## 2. Service Access Matrix

| Service / Role | `products/` | `users/` | `tryon/` | `temporary/` |
| :--- | :--- | :--- | :--- | :--- |
| **Shopper API** | Read (authorized) | Read/Write (owner only) | Read (owner only) | Upload staging |
| **Catalog API** | Read/Write (merchant) | Denied | Denied | Ingest staging |
| **VTO Worker** | Read (garment) | Read (authorized input) | Write/Read (results) | Read/Write (tryon) |
| **Ingest Worker** | Read/Write (products) | Denied | Denied | Read/Write (ingest) |
| **Maintenance Worker** | Limited | Delete (authorized erasure) | Delete (authorized erasure) | Delete (sweeps) |

---

## 3. IAM Policy Templates
The canonical IAM policy documents reside in `infra/aws/iam/policies/`:
- `dev-vto-s3.json` / `staging-vto-s3.json` / `prod-vto-s3.json`
- `dev-catalog-s3.json` / `staging-catalog-s3.json` / `prod-catalog-s3.json`

Example CLI command to apply an ECS task role policy:
```bash
aws iam put-role-policy \
  --role-name fashx-prod-vto-task-role \
  --policy-name fashx-prod-vto-s3-access \
  --policy-document file://infra/aws/iam/policies/prod-vto-s3.json
```
