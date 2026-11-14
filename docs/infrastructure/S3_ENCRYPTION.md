# FashXStudio — S3 Encryption Specification (Phase 03.4)

## 1. Overview
FashXStudio enforces dual-tier encryption across all object storage:
1. **At Rest**: Customer-managed AWS KMS keys (`sse_algorithm = "aws:kms"`) with S3 Bucket Keys enabled.
2. **In Transit**: HTTPS (TLS 1.2+) enforced via explicit bucket policy rejection of unencrypted transport (`aws:SecureTransport = "false"`).

---

## 2. Customer-Managed KMS Key Specification
Each environment utilizes an independent AWS KMS key created in Terraform (`infra/aws/s3/main.tf`):

| Environment | KMS Key Alias | Key Spec | Key Rotation | Deletion Window |
| :--- | :--- | :--- | :--- | :--- |
| **Development** | `alias/fashx-dev-s3` | SYMMETRIC_DEFAULT | Enabled (365d) | 30 days |
| **Staging** | `alias/fashx-staging-s3` | SYMMETRIC_DEFAULT | Enabled (365d) | 30 days |
| **Production** | `alias/fashx-prod-s3` | SYMMETRIC_DEFAULT | Enabled (365d) | 30 days |

### S3 Bucket Key Optimization
S3 Bucket Keys (`bucket_key_enabled = true`) are configured to reduce KMS request costs by up to 99% for presigned operations and worker batch jobs. Instead of invoking KMS on every GET/PUT, S3 caches short-lived bucket-level keys.

---

## 3. In-Transit Transport Enforcement (Bucket Policy)
Configured on every bucket to reject plaintext HTTP requests:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyInsecureTransport",
      "Effect": "Deny",
      "Principal": "*",
      "Action": "s3:*",
      "Resource": [
        "arn:aws:s3:::fashx-prod-private-ACCOUNT_ID",
        "arn:aws:s3:::fashx-prod-private-ACCOUNT_ID/*"
      ],
      "Condition": {
        "Bool": {
          "aws:SecureTransport": "false"
        }
      }
    }
  ]
}
```

---

## 4. Verification Procedures

```bash
# Verify KMS encryption on production bucket
aws s3api get-bucket-encryption \
  --bucket fashx-prod-private-ACCOUNT_ID \
  --region ap-south-1

# Verify KMS key rotation
aws kms get-key-rotation-status \
  --key-id alias/fashx-prod-s3 \
  --region ap-south-1

# Verify insecure transport rejection (HTTP request must return 403)
curl -i "http://fashx-prod-private-ACCOUNT_ID.s3.ap-south-1.amazonaws.com/test.txt"
```
