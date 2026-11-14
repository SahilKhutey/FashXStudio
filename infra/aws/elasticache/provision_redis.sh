#!/usr/bin/env bash
# ==============================================================================
# FASHXSTUDIO — PROVISION REDIS / VALKEY ELASTICACHE INSTANCE (PHASE 03.3)
# ==============================================================================
# Provisions an AWS ElastiCache Valkey/Redis instance in ap-south-1 (Mumbai)
# with TLS encryption in transit, AUTH token authentication stored in Secrets
# Manager, private subnet placement, and restricted security group ingress.
#
# Usage:
#   ENVIRONMENT=dev ./infra/aws/elasticache/provision_redis.sh
#   ENVIRONMENT=staging ./infra/aws/elasticache/provision_redis.sh
#   ENVIRONMENT=prod ./infra/aws/elasticache/provision_redis.sh
# ==============================================================================

set -euo pipefail

ENVIRONMENT="${ENVIRONMENT:-${1:-}}"
AWS_REGION="${AWS_REGION:-ap-south-1}"

if [[ -z "${ENVIRONMENT}" ]]; then
  echo "ERROR: ENVIRONMENT is required. Allowed values: dev, staging, prod" >&2
  exit 1
fi

case "${ENVIRONMENT}" in
  dev)
    CLUSTER_ID="fashx-dev-redis"
    NODE_TYPE="cache.t4g.micro"
    NUM_NODES=1
    MULTI_AZ="false"
    AUTOMATIC_FAILOVER="false"
    TRANSIT_ENCRYPTION="true"
    AT_REST_ENCRYPTION="false"
    SNAPSHOT_RETENTION=0
    ;;
  staging)
    CLUSTER_ID="fashx-staging-redis"
    NODE_TYPE="cache.t4g.small"
    NUM_NODES=2
    MULTI_AZ="false"
    AUTOMATIC_FAILOVER="true"
    TRANSIT_ENCRYPTION="true"
    AT_REST_ENCRYPTION="true"
    SNAPSHOT_RETENTION=7
    ;;
  prod)
    CLUSTER_ID="fashx-prod-redis"
    NODE_TYPE="cache.t4g.medium"
    NUM_NODES=3
    MULTI_AZ="true"
    AUTOMATIC_FAILOVER="true"
    TRANSIT_ENCRYPTION="true"
    AT_REST_ENCRYPTION="true"
    SNAPSHOT_RETENTION=14
    ;;
  *)
    echo "ERROR: Invalid ENVIRONMENT '${ENVIRONMENT}'. Allowed values: dev, staging, prod" >&2
    exit 1
    ;;
esac

SECRET_ID_AUTH="/fashx/${ENVIRONMENT}/redis/auth_token"
SECRET_ID_URL="/fashx/${ENVIRONMENT}/redis/url"
SUBNET_GROUP="fashx-redis-subnet-group"
SECURITY_GROUP_NAME="fashx-redis-sg"

echo "=============================================================================="
echo "FashXStudio ElastiCache Provisioning"
echo "Environment:        ${ENVIRONMENT}"
echo "Cluster Identifier: ${CLUSTER_ID}"
echo "Region:             ${AWS_REGION}"
echo "Node Type:          ${NODE_TYPE}"
echo "Nodes:              ${NUM_NODES}"
echo "Multi-AZ:           ${MULTI_AZ}"
echo "Transit Encryption: ${TRANSIT_ENCRYPTION}"
echo "=============================================================================="

# 1. Fetch or generate AUTH token from AWS Secrets Manager
echo "Resolving Redis AUTH token from Secrets Manager: ${SECRET_ID_AUTH}..."
AUTH_TOKEN=""
if aws secretsmanager describe-secret --secret-id "${SECRET_ID_AUTH}" --region "${AWS_REGION}" >/dev/null 2>&1; then
  AUTH_TOKEN=$(aws secretsmanager get-secret-value --secret-id "${SECRET_ID_AUTH}" --region "${AWS_REGION}" --query "SecretString" --output text)
  echo "Found existing AUTH token in Secrets Manager."
else
  echo "Generating new cryptographically secure AUTH token..."
  AUTH_TOKEN=$(openssl rand -hex 32)
  aws secretsmanager create-secret \
    --name "${SECRET_ID_AUTH}" \
    --description "ElastiCache Redis AUTH token for ${ENVIRONMENT}" \
    --secret-string "${AUTH_TOKEN}" \
    --region "${AWS_REGION}" \
    --tags Key=Environment,Value="${ENVIRONMENT}" Key=Project,Value=FashXStudio >/dev/null
  echo "Stored new AUTH token in Secrets Manager."
fi

# 2. Resolve Security Group ID
SG_ID=$(aws ec2 describe-security-groups \
  --filters "Name=group-name,Values=${SECURITY_GROUP_NAME}" \
  --region "${AWS_REGION}" \
  --query "SecurityGroups[0].GroupId" \
  --output text)

if [[ -z "${SG_ID}" || "${SG_ID}" == "None" ]]; then
  echo "ERROR: Security group '${SECURITY_GROUP_NAME}' not found in region ${AWS_REGION}." >&2
  exit 1
fi

echo "Security Group: ${SG_ID}"

# 3. Create or Update Replication Group
EXISTS=$(aws elasticache describe-replication-groups \
  --replication-group-id "${CLUSTER_ID}" \
  --region "${AWS_REGION}" \
  --query "ReplicationGroups[0].Status" \
  --output text 2>/dev/null || echo "NOT_FOUND")

if [[ "${EXISTS}" == "NOT_FOUND" ]]; then
  echo "Creating ElastiCache replication group '${CLUSTER_ID}'..."

  CREATE_ARGS=(
    --replication-group-id "${CLUSTER_ID}"
    --replication-group-description "FashXStudio ${ENVIRONMENT} Redis Broker"
    --engine "redis"
    --engine-version "7.1"
    --cache-node-type "${NODE_TYPE}"
    --cache-subnet-group-name "${SUBNET_GROUP}"
    --security-group-ids "${SG_ID}"
    --port 6379
    --region "${AWS_REGION}"
    --tags Key=Environment,Value="${ENVIRONMENT}" Key=Project,Value=FashXStudio
  )

  if [[ "${NUM_NODES}" -gt 1 ]]; then
    CREATE_ARGS+=(--num-cache-clusters "${NUM_NODES}")
  fi

  if [[ "${AUTOMATIC_FAILOVER}" == "true" ]]; then
    CREATE_ARGS+=(--automatic-failover-enabled)
  fi

  if [[ "${MULTI_AZ}" == "true" ]]; then
    CREATE_ARGS+=(--multi-az-enabled)
  fi

  if [[ "${TRANSIT_ENCRYPTION}" == "true" ]]; then
    CREATE_ARGS+=(--transit-encryption-enabled --auth-token "${AUTH_TOKEN}")
  fi

  if [[ "${AT_REST_ENCRYPTION}" == "true" ]]; then
    CREATE_ARGS+=(--at-rest-encryption-enabled)
  fi

  if [[ "${SNAPSHOT_RETENTION}" -gt 0 ]]; then
    CREATE_ARGS+=(--snapshot-retention-limit "${SNAPSHOT_RETENTION}" --snapshot-window "03:00-04:00")
  fi

  aws elasticache create-replication-group "${CREATE_ARGS[@]}" >/dev/null
  echo "Replication group creation initiated."
else
  echo "Replication group '${CLUSTER_ID}' already exists (status: ${EXISTS})."
fi

echo "Waiting for replication group '${CLUSTER_ID}' to become available..."
aws elasticache wait replication-group-available \
  --replication-group-id "${CLUSTER_ID}" \
  --region "${AWS_REGION}"

# 4. Fetch Primary Endpoint
PRIMARY_ENDPOINT=$(aws elasticache describe-replication-groups \
  --replication-group-id "${CLUSTER_ID}" \
  --region "${AWS_REGION}" \
  --query "ReplicationGroups[0].NodeGroups[0].PrimaryEndpoint.Address" \
  --output text)

echo "Primary Redis Endpoint: ${PRIMARY_ENDPOINT}"

# 5. Construct and publish REDIS_URL secret
SCHEME="rediss"
if [[ "${TRANSIT_ENCRYPTION}" != "true" ]]; then
  SCHEME="redis"
fi

REDIS_URL="${SCHEME}://:${AUTH_TOKEN}@${PRIMARY_ENDPOINT}:6379/0"

echo "Publishing REDIS_URL secret to ${SECRET_ID_URL}..."
if aws secretsmanager describe-secret --secret-id "${SECRET_ID_URL}" --region "${AWS_REGION}" >/dev/null 2>&1; then
  aws secretsmanager put-secret-value \
    --secret-id "${SECRET_ID_URL}" \
    --secret-string "${REDIS_URL}" \
    --region "${AWS_REGION}" >/dev/null
else
  aws secretsmanager create-secret \
    --name "${SECRET_ID_URL}" \
    --description "Celery Broker REDIS_URL for ${ENVIRONMENT}" \
    --secret-string "${REDIS_URL}" \
    --region "${AWS_REGION}" \
    --tags Key=Environment,Value="${ENVIRONMENT}" Key=Project,Value=FashXStudio >/dev/null
fi

echo "=============================================================================="
echo "ElastiCache Redis provisioned successfully for ${ENVIRONMENT}."
echo "Secret Published: ${SECRET_ID_URL}"
echo "=============================================================================="
