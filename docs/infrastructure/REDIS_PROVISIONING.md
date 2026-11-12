# Redis Cluster Provisioning Guide

> **Operational runbook. Pre-pilot status maintained per AGENTS.md.**

---

## 1. Prerequisites

Before executing provisioning steps, ensure the following AWS infrastructure is available:
1. VPC deployed in `ap-south-1` with at least 2 private subnets across distinct Availability Zones (`ap-south-1a`, `ap-south-1b`, `ap-south-1c`).
2. Security group for backend application servers and Celery workers (`fashx-app-sg`).
3. S3 remote state bucket for Terraform (`fashx-terraform-state-ap-south-1`).

---

## 2. Infrastructure as Code Provisioning (Terraform)

The canonical IaC configurations are located in `infra/aws/elasticache/`.

### Step 1: Configure Variables
Copy `terraform.tfvars.example` to `terraform.tfvars`:
```bash
cp infra/aws/elasticache/terraform.tfvars.example infra/aws/elasticache/terraform.tfvars
```
Populate VPC and private subnet identifiers:
```hcl
aws_region = "ap-south-1"
vpc_id     = "vpc-0123456789abcdef0"

cache_subnet_ids = [
  "subnet-0123456789abcdef1",
  "subnet-0123456789abcdef2",
  "subnet-0123456789abcdef3"
]

app_security_group_ids = [
  "sg-0123456789abcdef0"
]
```

### Step 2: Initialize & Validate
```bash
cd infra/aws/elasticache
terraform init
terraform validate
```

### Step 3: Plan & Apply
```bash
terraform plan -out=elasticache.tfplan
terraform apply elasticache.tfplan
```

---

## 3. Post-Provisioning Verification

Verify cluster health and status using the verification script:
```bash
# Verify Staging cluster
./scripts/redis/verify_redis.sh staging

# Verify Production cluster
./scripts/redis/verify_redis.sh prod
```

Inspect Celery task routing and broker connection:
```bash
python scripts/redis/test_celery_queues.py
```
