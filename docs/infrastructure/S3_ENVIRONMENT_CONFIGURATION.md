# FashXStudio — S3 Environment Configuration Runbook (Phase 03.4)

## 1. Environment Bucket Matrix

| Environment | Bucket Identifier | KMS Key Alias | Region | Public Access |
| :--- | :--- | :--- | :--- | :--- |
| **Development** | `fashx-dev-private-ACCOUNT_ID` | `alias/fashx-dev-s3` | `ap-south-1` | Blocked (All 4) |
| **Staging** | `fashx-staging-private-ACCOUNT_ID` | `alias/fashx-staging-s3` | `ap-south-1` | Blocked (All 4) |
| **Production** | `fashx-prod-private-ACCOUNT_ID` | `alias/fashx-prod-s3` | `ap-south-1` | Blocked (All 4) |

---

## 2. Terraform Provisioning Commands
The Terraform infrastructure configuration resides at `infra/aws/s3/main.tf`.

```bash
cd infra/aws/s3
terraform init
terraform fmt -check
terraform validate
terraform plan -out=s3.tfplan
terraform apply s3.tfplan
```

---

## 3. Post-Provisioning Verification Commands
Run the following verification checks using the AWS CLI for each environment bucket:

```bash
# 1. Verify bucket existence
aws s3api list-buckets --query "Buckets[?starts_with(Name, 'fashx-')].Name" --output table

# 2. Verify Block Public Access settings (all 4 must be true)
aws s3api get-public-access-block \
  --bucket fashx-prod-private-ACCOUNT_ID \
  --region ap-south-1

# 3. Verify Bucket Owner Enforced (ACLs disabled)
aws s3api get-bucket-ownership-controls \
  --bucket fashx-prod-private-ACCOUNT_ID \
  --region ap-south-1

# 4. Verify SSE-KMS Default Encryption
aws s3api get-bucket-encryption \
  --bucket fashx-prod-private-ACCOUNT_ID \
  --region ap-south-1

# 5. Verify Lifecycle Rules (temporary 1d, tryon 30d)
aws s3api get-bucket-lifecycle-configuration \
  --bucket fashx-prod-private-ACCOUNT_ID \
  --region ap-south-1

# 6. Verify KMS Key Rotation
aws kms get-key-rotation-status \
  --key-id alias/fashx-prod-s3 \
  --region ap-south-1
```

---

## 4. Application Configuration Variables
Configure ECS container environment variables for each tier:

```bash
STORAGE_BACKEND=s3
S3_USE_IAM_ROLE=true
S3_BUCKET=fashx-prod-private-ACCOUNT_ID
S3_REGION=ap-south-1
S3_KMS_KEY_ID=arn:aws:kms:ap-south-1:ACCOUNT_ID:alias/fashx-prod-s3
S3_PRESIGNED_UPLOAD_TTL_SECONDS=300
S3_PRESIGNED_DOWNLOAD_TTL_SECONDS=300
```
