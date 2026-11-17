#!/usr/bin/env bash
# ==============================================================================
# FashXStudio Infrastructure Deployment Script
# Target: AWS ap-south-1 (Mumbai)
# Platform: Amazon ECS Fargate
# ==============================================================================
set -euo pipefail

ENVIRONMENT="${1:-staging}"
IMAGE_URI="${2:-}"

if [ -z "$IMAGE_URI" ]; then
  echo "Usage: $0 <environment> <image_uri>"
  echo "Example: $0 staging 123456789012.dkr.ecr.ap-south-1.amazonaws.com/fashx-backend@sha256:abc..."
  exit 1
fi

echo "=========================================================="
echo " Starting Deployment for Environment: $ENVIRONMENT"
echo " Image URI: $IMAGE_URI"
echo "=========================================================="

CLUSTER="fashx-${ENVIRONMENT}"
ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)"

# 1. Run database migration task
echo "[1/4] Executing database migration task..."
bash infra/aws/scripts/run_migrations.sh "$ENVIRONMENT" "$IMAGE_URI"

# 2. Deploy ECS services
echo "[2/4] Deploying ECS services with circuit breaker..."
API_SERVICE="fashx-${ENVIRONMENT}-api"
TRYON_SERVICE="fashx-${ENVIRONMENT}-tryon"
INGEST_SERVICE="fashx-${ENVIRONMENT}-ingest"
BEAT_SERVICE="fashx-${ENVIRONMENT}-beat"

deploy_service() {
  local service="$1"
  local template="$2"
  local container="$3"

  local tmpfile
  tmpfile="$(mktemp)"
  sed \
    -e "s|\${ACCOUNT_ID}|$ACCOUNT_ID|g" \
    "$template" > "$tmpfile"

  jq --arg img "$IMAGE_URI" --arg c "$container" \
    '.containerDefinitions |= map(if .name == $c then .image = $img else . end)' \
    "$tmpfile" > "${tmpfile}.rendered"

  local task_arn
  task_arn="$(aws ecs register-task-definition --cli-input-json "file://${tmpfile}.rendered" --query 'taskDefinition.taskDefinitionArn' --output text)"
  rm -f "$tmpfile" "${tmpfile}.rendered"

  echo "Updating $service to $task_arn..."
  aws ecs update-service \
    --cluster "$CLUSTER" \
    --service "$service" \
    --task-definition "$task_arn" \
    --deployment-configuration "deploymentCircuitBreaker={enable=true,rollback=true},minimumHealthyPercent=100,maximumPercent=200" \
    >/dev/null
}

TPL_ENV="$ENVIRONMENT"
if [ "$ENVIRONMENT" = "prod" ]; then
  TPL_ENV="production"
fi

deploy_service "$API_SERVICE" "infra/aws/ecs/task-definitions/api-${TPL_ENV}.json" "fashx-api"
deploy_service "$TRYON_SERVICE" "infra/aws/ecs/task-definitions/tryon-${TPL_ENV}.json" "fashx-tryon"
deploy_service "$INGEST_SERVICE" "infra/aws/ecs/task-definitions/ingest-${TPL_ENV}.json" "fashx-ingest"
deploy_service "$BEAT_SERVICE" "infra/aws/ecs/task-definitions/beat-${TPL_ENV}.json" "fashx-beat"

# 3. Wait for services to stabilize
echo "[3/4] Waiting for ECS services to stabilize..."
aws ecs wait services-stable \
  --cluster "$CLUSTER" \
  --services "$API_SERVICE" "$TRYON_SERVICE" "$INGEST_SERVICE" "$BEAT_SERVICE"
echo "All ECS services stabilized successfully."

# 4. Post-deployment smoke check
echo "[4/4] Executing smoke tests..."
if [ -n "${API_BASE:-}" ]; then
  python scripts/release/smoke.py --base "$API_BASE"
else
  echo "Notice: API_BASE not set. Direct HTTP smoke tests skipped."
fi

echo "=========================================================="
echo " Deployment Complete for $ENVIRONMENT"
echo "=========================================================="
