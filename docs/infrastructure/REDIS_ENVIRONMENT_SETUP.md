# FashXStudio — Redis Environment Setup Runbook (Phase 03.3)

## 1. Prerequisites
Before executing ElastiCache provisioning:
1. Ensure the AWS CLI is configured with credentials authorized for `elasticache:*`, `secretsmanager:*`, and `ec2:Describe*`.
2. Ensure the base VPC, private subnets, and subnet group `fashx-redis-subnet-group` exist in `ap-south-1`.
3. Ensure security group `fashx-redis-sg` exists and authorizes ingress on port 6379 from ECS tasks.

---

## 2. Automated Provisioning via Bash Script
The repository provides an idempotent provisioning script at `infra/aws/elasticache/provision_redis.sh`.

### Development Environment
```bash
ENVIRONMENT=dev ./infra/aws/elasticache/provision_redis.sh
```
- Cluster ID: `fashx-dev-redis`
- Node Type: `cache.t4g.micro` (1 node)
- Encryption: TLS enabled, single node, AUTH token generated and stored in Secrets Manager.

### Staging Environment
```bash
ENVIRONMENT=staging ./infra/aws/elasticache/provision_redis.sh
```
- Cluster ID: `fashx-staging-redis`
- Node Type: `cache.t4g.small` (2 nodes, primary + replica)
- Automatic Failover: Enabled.
- Encryption: TLS enabled, at-rest encryption enabled, 7-day snapshot retention.

### Production Environment
```bash
ENVIRONMENT=prod ./infra/aws/elasticache/provision_redis.sh
```
- Cluster ID: `fashx-prod-redis`
- Node Type: `cache.t4g.medium` (3 nodes, primary + 2 replicas)
- Automatic Failover: Enabled.
- Multi-AZ: Enabled.
- Encryption: TLS enabled, KMS at-rest encryption enabled, 14-day snapshot retention.

---

## 3. Provisioning via Terraform
Alternatively, provision the full cluster tier using Terraform:

```bash
cd infra/aws/elasticache
terraform init
terraform plan -var-file="terraform.tfvars"
terraform apply -var-file="terraform.tfvars"
```

Verify outputs:
```bash
terraform output redis_primary_endpoint_prod
terraform output redis_url_secret_arn_prod
```

---

## 4. Secret Verification in AWS Secrets Manager
After cluster creation, verify that the broker URL secret is published and available:

```bash
aws secretsmanager get-secret-value \
  --secret-id "/fashx/staging/redis/url" \
  --region ap-south-1 \
  --query "SecretString" \
  --output text
```

Expected format:
```text
rediss://:<AUTH_TOKEN>@fashx-staging-redis.xxxxxx.0001.aps1.cache.amazonaws.com:6379/0
```

---

## 5. Connectivity Testing from ECS Bastion / Task
To verify in-VPC TLS connectivity without exposing Redis publicly:

```bash
# Using redis-cli with TLS and AUTH
redis-cli -h <PRIMARY_ENDPOINT> -p 6379 --tls -a <AUTH_TOKEN> PING
# Expected response: PONG

# Verify SSL handshake
openssl s_client -connect <PRIMARY_ENDPOINT>:6379 -starttls redis
```
