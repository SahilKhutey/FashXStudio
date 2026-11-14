#!/usr/bin/env bash
# scripts/release/rollback_ecs.sh
# Emergency or automated rollback script for FashX ECS services.
# Reverts ECS services to their previous known-good task definition revisions.

set -euo pipefail

ENVIRONMENT="${1:?Usage: rollback_ecs.sh <dev|staging|prod> [STATE_FILE]}"
STATE_FILE="${2:-}"
REGION="${AWS_REGION:-ap-south-1}"

echo "[*] Initiating ECS rollback for environment: ${ENVIRONMENT}"

case "$ENVIRONMENT" in
  dev|development)
    CLUSTER="${ECS_CLUSTER:-fashx-dev}"
    SERVICES=(
      "${ECS_API_SERVICE:-fashx-dev-api}"
      "${ECS_TRYON_SERVICE:-fashx-dev-tryon}"
      "${ECS_INGEST_SERVICE:-fashx-dev-ingest}"
      "${ECS_BEAT_SERVICE:-fashx-dev-beat}"
    )
    ;;
  staging)
    CLUSTER="${ECS_CLUSTER:-fashx-staging}"
    SERVICES=(
      "${ECS_API_SERVICE:-fashx-staging-api}"
      "${ECS_TRYON_SERVICE:-fashx-staging-tryon}"
      "${ECS_INGEST_SERVICE:-fashx-staging-ingest}"
      "${ECS_BEAT_SERVICE:-fashx-staging-beat}"
    )
    ;;
  prod|production)
    CLUSTER="${ECS_CLUSTER:-fashx-prod}"
    SERVICES=(
      "${ECS_API_SERVICE:-fashx-prod-api}"
      "${ECS_TRYON_SERVICE:-fashx-prod-tryon}"
      "${ECS_INGEST_SERVICE:-fashx-prod-ingest}"
      "${ECS_BEAT_SERVICE:-fashx-prod-beat}"
    )
    ;;
  *)
    echo "[-] Error: Invalid environment '${ENVIRONMENT}'. Must be dev, staging, or prod." >&2
    exit 2
    ;;
esac

echo "[*] Target ECS Cluster: ${CLUSTER}"

# If a state file was captured before deployment, use those exact task definition ARNs.
# Otherwise, inspect each service's previous task definition or active deployment.
for SERVICE in "${SERVICES[@]}"; do
  PREV_TASK_DEF=""
  if [[ -n "$STATE_FILE" && -f "$STATE_FILE" ]]; then
    PREV_TASK_DEF="$(jq -r --arg svc "$SERVICE" '.[$svc] // empty' "$STATE_FILE")"
  fi

  if [[ -z "$PREV_TASK_DEF" ]]; then
    echo "[*] Querying current task definition for service: ${SERVICE}"
    CURRENT_TASK_DEF="$(
      aws ecs describe-services \
        --region "$REGION" \
        --cluster "$CLUSTER" \
        --services "$SERVICE" \
        --query 'services[0].taskDefinition' \
        --output text
    )"
    
    # Extract family and revision
    FAMILY="$(echo "$CURRENT_TASK_DEF" | awk -F'/' '{print $NF}' | cut -d':' -f1)"
    CURRENT_REV="$(echo "$CURRENT_TASK_DEF" | awk -F':' '{print $NF}')"
    
    if [[ "$CURRENT_REV" -gt 1 ]]; then
      PREV_REV=$((CURRENT_REV - 1))
      PREV_TASK_DEF="${FAMILY}:${PREV_REV}"
    else
      echo "[-] Warning: Service ${SERVICE} is at revision 1. Cannot decrement revision." >&2
      PREV_TASK_DEF="$CURRENT_TASK_DEF"
    fi
  fi

  echo "[*] Rolling back ${SERVICE} to task definition: ${PREV_TASK_DEF}"
  aws ecs update-service \
    --region "$REGION" \
    --cluster "$CLUSTER" \
    --service "$SERVICE" \
    --task-definition "$PREV_TASK_DEF" \
    --force-new-deployment \
    --deployment-configuration "deploymentCircuitBreaker={enable=true,rollback=true},minimumHealthyPercent=100,maximumPercent=200" \
    >/dev/null
done

echo "[*] Waiting for services to stabilize after rollback..."
aws ecs wait services-stable \
  --region "$REGION" \
  --cluster "$CLUSTER" \
  --services "${SERVICES[@]}"

echo "[+] All ECS services in cluster ${CLUSTER} rolled back and stable."

if [[ -n "${API_BASE:-}" ]]; then
  echo "[*] Running post-rollback smoke verification against ${API_BASE}..."
  python scripts/release/smoke.py --base "${API_BASE}"
fi
