#!/usr/bin/env bash
# ==============================================================================
# FashXStudio One-Off Migration Runner (ECS Fargate)
# ==============================================================================
set -euo pipefail

ENVIRONMENT="${1:-staging}"
IMAGE_URI="${2:-}"

if [ -z "$IMAGE_URI" ]; then
  echo "Usage: $0 <environment> <image_uri>"
  exit 1
fi

CLUSTER="fashx-${ENVIRONMENT}"
ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)"

TPL_ENV="$ENVIRONMENT"
if [ "$ENVIRONMENT" = "prod" ]; then
  TPL_ENV="production"
fi

TASK_DEF_FILE="$(mktemp)"
sed \
  -e "s|\${ACCOUNT_ID}|$ACCOUNT_ID|g" \
  "infra/aws/ecs/task-definitions/migration-${TPL_ENV}.json" > "$TASK_DEF_FILE"

jq --arg img "$IMAGE_URI" '.containerDefinitions[0].image = $img' "$TASK_DEF_FILE" > "${TASK_DEF_FILE}.rendered"
MIGRATION_TASK_ARN="$(aws ecs register-task-definition --cli-input-json "file://${TASK_DEF_FILE}.rendered" --query 'taskDefinition.taskDefinitionArn' --output text)"
rm -f "$TASK_DEF_FILE" "${TASK_DEF_FILE}.rendered"

echo "Running one-off migration task: $MIGRATION_TASK_ARN"
RUN_ARN="$(aws ecs run-task \
  --cluster "$CLUSTER" \
  --launch-type FARGATE \
  --task-definition "$MIGRATION_TASK_ARN" \
  --network-configuration "awsvpcConfiguration={subnets=[${ECS_SUBNETS:-}],securityGroups=[${ECS_SECURITY_GROUPS:-}],assignPublicIp=DISABLED}" \
  --query 'tasks[0].taskArn' \
  --output text)"

if [ "$RUN_ARN" = "None" ] || [ -z "$RUN_ARN" ]; then
  echo "ERROR: Failed to run migration task."
  exit 1
fi

echo "Waiting for migration task $RUN_ARN to complete..."
aws ecs wait tasks-stopped --cluster "$CLUSTER" --tasks "$RUN_ARN"

EXIT_CODE="$(aws ecs describe-tasks --cluster "$CLUSTER" --tasks "$RUN_ARN" --query 'tasks[0].containers[0].exitCode' --output text)"
if [ "$EXIT_CODE" != "0" ]; then
  echo "ERROR: Database migration failed with exit code $EXIT_CODE."
  exit 1
fi

echo "Database migration completed successfully (exit code 0)."
