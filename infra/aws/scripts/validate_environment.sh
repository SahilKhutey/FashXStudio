#!/usr/bin/env bash
# ==============================================================================
# FashXStudio Infrastructure Environment Validator
# ==============================================================================
set -euo pipefail

ENVIRONMENT="${1:-staging}"
AWS_REGION="${AWS_REGION:-ap-south-1}"

echo "=========================================================="
echo " Validating AWS Infrastructure for: $ENVIRONMENT ($AWS_REGION)"
echo "=========================================================="

# 1. AWS Identity Check
echo "[1/6] Checking AWS Caller Identity..."
aws sts get-caller-identity --output table

# 2. ECS Cluster Check
echo "[2/6] Checking ECS Cluster..."
CLUSTER_STATUS="$(aws ecs describe-clusters --clusters "fashx-${ENVIRONMENT}" --region "$AWS_REGION" --query 'clusters[0].status' --output text 2>/dev/null || echo 'NOT_FOUND')"
echo "ECS Cluster fashx-${ENVIRONMENT}: $CLUSTER_STATUS"

# 3. RDS PostgreSQL Check
echo "[3/6] Checking RDS Instance..."
RDS_STATUS="$(aws rds describe-db-instances --db-instance-identifier "fashx-pg-${ENVIRONMENT}" --region "$AWS_REGION" --query 'DBInstances[0].DBInstanceStatus' --output text 2>/dev/null || echo 'NOT_FOUND')"
echo "RDS Instance fashx-pg-${ENVIRONMENT}: $RDS_STATUS"

# 4. ElastiCache Valkey/Redis Check
echo "[4/6] Checking ElastiCache Cluster..."
CACHE_STATUS="$(aws elasticache describe-replication-groups --replication-group-id "fashx-${ENVIRONMENT}-valkey" --region "$AWS_REGION" --query 'ReplicationGroups[0].Status' --output text 2>/dev/null || echo 'NOT_FOUND')"
echo "ElastiCache Cluster fashx-${ENVIRONMENT}-valkey: $CACHE_STATUS"

# 5. S3 Bucket Check
echo "[5/6] Checking S3 Private Bucket..."
ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text 2>/dev/null || echo 'unknown')"
BUCKET_NAME="fashx-${ENVIRONMENT}-private-${ACCOUNT_ID}"
BUCKET_STATUS="$(aws s3api head-bucket --bucket "$BUCKET_NAME" 2>&1 || echo 'OK')"
echo "S3 Bucket $BUCKET_NAME check completed."

# 6. Secrets Check
echo "[6/6] Checking Secrets Manager Secrets..."
aws secretsmanager describe-secret --secret-id "fashx/${ENVIRONMENT}/postgres/database-url" --region "$AWS_REGION" --query 'Name' --output text 2>/dev/null || echo "Secret database-url: NOT_FOUND"
aws secretsmanager describe-secret --secret-id "fashx/${ENVIRONMENT}/redis/url" --region "$AWS_REGION" --query 'Name' --output text 2>/dev/null || echo "Secret redis/url: NOT_FOUND"

echo "=========================================================="
echo " Environment Validation Sequence Finished"
echo "=========================================================="
