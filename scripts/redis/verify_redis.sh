#!/usr/bin/env bash
# ==============================================================================
# FashXStudio — AWS ElastiCache for Redis Cluster Verification Utility
# ==============================================================================
# Usage:
#   ./scripts/redis/verify_redis.sh dev
#   ./scripts/redis/verify_redis.sh staging
#   ./scripts/redis/verify_redis.sh prod
# ==============================================================================

set -euo pipefail

ENV_TARGET="${1:-dev}"
REGION="${AWS_REGION:-ap-south-1}"

echo "=================================================================="
echo "FASHXSTUDIO ELASTICACHE REDIS VERIFICATION: [${ENV_TARGET}]"
echo "Region: ${REGION}"
echo "=================================================================="

CLUSTER_ID="fashx-redis-${ENV_TARGET}"

if command -v aws >/dev/null 2>&1; then
  echo "--- 1. Querying AWS ElastiCache Status for ${CLUSTER_ID} ---"
  aws elasticache describe-replication-groups \
    --replication-group-id "${CLUSTER_ID}" \
    --region "${REGION}" \
    --query 'ReplicationGroups[0].{ID:ReplicationGroupId,Status:Status,MultiAZ:MultiAZ,TransitEncryption:TransitEncryptionEnabled,AtRestEncryption:AtRestEncryptionEnabled,AuthTokenEnabled:AuthTokenEnabled,NodeCount:MemberClusters}' \
    --output table || {
      echo "WARNING: Could not query ElastiCache via AWS CLI."
    }
else
  echo "INFO: AWS CLI not found on PATH. Skipping cloud metadata query."
fi

# Connect using redis-cli or redis-py if environment variables are set
REDIS_HOST="${REDIS_HOST:-localhost}"
REDIS_PORT="${REDIS_PORT:-6379}"
AUTH_TOKEN="${REDIS_AUTH_TOKEN:-}"

echo ""
echo "--- 2. Direct Redis Health Check ---"
echo "Target: ${REDIS_HOST}:${REDIS_PORT}"

python - <<EOF
import os
import sys
import asyncio

async def test_redis():
    host = os.environ.get("REDIS_HOST", "localhost")
    port = int(os.environ.get("REDIS_PORT", "6379"))
    auth = os.environ.get("REDIS_AUTH_TOKEN")
    ssl_enabled = "${ENV_TARGET}" in ["staging", "prod"]

    scheme = "rediss" if ssl_enabled else "redis"
    auth_part = f":{auth}@" if auth else ""
    url = f"{scheme}://{auth_part}{host}:{port}/0"

    print(f"Connecting to: {scheme}://***@{host}:{port}/0 (ssl={ssl_enabled})")

    try:
        import redis.asyncio as aioredis
        client = aioredis.from_url(url, socket_timeout=3.0)
        pong = await client.ping()
        print(f"PING response: {pong}")
        info = await client.info()
        print(f"Redis Version: {info.get('redis_version', 'unknown')}")
        print(f"Role: {info.get('role', 'unknown')}")
        print(f"Connected Clients: {info.get('connected_clients', 'unknown')}")
        print(f"Used Memory Human: {info.get('used_memory_human', 'unknown')}")
        print(f"Max Memory Human: {info.get('maxmemory_human', '0B')}")
        print(f"Max Memory Policy: {info.get('maxmemory_policy', 'unknown')}")
        await client.aclose()
        print("VERIFICATION RESULT: REDIS OK")
    except Exception as e:
        print(f"Connection error: {e}")
        print("Note: If cluster is not yet provisioned in AWS or offline, this is expected.")

asyncio.run(test_redis())
EOF

echo "=================================================================="
echo "Verification protocol concluded."
echo "=================================================================="
