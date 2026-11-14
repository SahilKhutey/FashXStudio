#!/usr/bin/env bash
set -Eeuo pipefail

ENVIRONMENT="${1:?Usage: promote_ecs.sh dev|staging|prod IMAGE_TAG}"
IMAGE_TAG="${2:?Image tag required}"
REGION="ap-south-1"
ECR_REPOSITORY="fashx"

case "$ENVIRONMENT" in
  dev)
    CLUSTER="fashx-dev"
    API_SERVICE="fashx-dev-api"
    TRYON_SERVICE="fashx-dev-tryon"
    INGEST_SERVICE="fashx-dev-ingest"
    BEAT_SERVICE="fashx-dev-beat"
    MIGRATION_FAMILY="fashx-dev-migration"
    API_FAMILY="fashx-dev-api"
    TRYON_FAMILY="fashx-dev-tryon"
    INGEST_FAMILY="fashx-dev-ingest"
    BEAT_FAMILY="fashx-dev-beat"
    ;;
  staging)
    CLUSTER="fashx-staging"
    API_SERVICE="fashx-staging-api"
    TRYON_SERVICE="fashx-staging-tryon"
    INGEST_SERVICE="fashx-staging-ingest"
    BEAT_SERVICE="fashx-staging-beat"
    MIGRATION_FAMILY="fashx-staging-migration"
    API_FAMILY="fashx-staging-api"
    TRYON_FAMILY="fashx-staging-tryon"
    INGEST_FAMILY="fashx-staging-ingest"
    BEAT_FAMILY="fashx-staging-beat"
    ;;
  prod)
    CLUSTER="fashx-prod"
    API_SERVICE="fashx-prod-api"
    TRYON_SERVICE="fashx-prod-tryon"
    INGEST_SERVICE="fashx-prod-ingest"
    BEAT_SERVICE="fashx-prod-beat"
    MIGRATION_FAMILY="fashx-prod-migration"
    API_FAMILY="fashx-prod-api"
    TRYON_FAMILY="fashx-prod-tryon"
    INGEST_FAMILY="fashx-prod-ingest"
    BEAT_FAMILY="fashx-prod-beat"
    ;;
  *)
    echo "Invalid environment: $ENVIRONMENT" >&2
    exit 2
    ;;
esac

: "${ECS_SUBNETS:?Set comma-separated private subnet IDs}"
: "${ECS_SECURITY_GROUP:?Set the environment ECS security group}"
: "${API_BASE:?Set the environment API base URL}"

ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)"
REGISTRY="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com"

DIGEST="$(
  aws ecr describe-images \
    --region "$REGION" \
    --repository-name "$ECR_REPOSITORY" \
    --image-ids "imageTag=${IMAGE_TAG}" \
    --query 'imageDetails[0].imageDigest' \
    --output text
)"

if [[ -z "$DIGEST" || "$DIGEST" == "None" ]]; then
  echo "Image digest not found." >&2
  exit 1
fi

IMAGE_URI="${REGISTRY}/${ECR_REPOSITORY}@${DIGEST}"
echo "Promoting ${IMAGE_URI} to ${ENVIRONMENT}"

register_task_definition() {
  local family="$1"
  local container_name="$2"
  local output_file
  output_file="$(mktemp)"

  aws ecs describe-task-definition \
    --region "$REGION" \
    --task-definition "$family" \
    --query taskDefinition \
    --output json | jq \
    --arg image "$IMAGE_URI" \
    --arg container "$container_name" '
      .containerDefinitions |= map(
        if (.name == $container or .name == ("fashx-" + $container) or ($container == "worker" and (.name == "fashx-tryon" or .name == "fashx-ingest")) or ($container == "migration" and .name == "fashx-migrate")) then .image = $image else . end
      )
      | del(
        .taskDefinitionArn,
        .revision,
        .status,
        .requiresAttributes,
        .compatibilities,
        .registeredAt,
        .registeredBy,
        .deregisteredAt
      )
    ' > "$output_file"

  local arn
  arn="$(
    aws ecs register-task-definition \
      --region "$REGION" \
      --cli-input-json "file://${output_file}" \
      --query 'taskDefinition.taskDefinitionArn' \
      --output text
  )"
  rm -f "$output_file"
  echo "$arn"
}

MIGRATION_TASK="$(register_task_definition "$MIGRATION_FAMILY" migration)"

TASK_ARN="$(
  aws ecs run-task \
    --region "$REGION" \
    --cluster "$CLUSTER" \
    --launch-type FARGATE \
    --task-definition "$MIGRATION_TASK" \
    --network-configuration \
    "awsvpcConfiguration={subnets=[${ECS_SUBNETS}],securityGroups=[${ECS_SECURITY_GROUP}],assignPublicIp=DISABLED}" \
    --query 'tasks[0].taskArn' \
    --output text
)"

if [[ -z "$TASK_ARN" || "$TASK_ARN" == "None" ]]; then
  echo "Migration task failed to start." >&2
  exit 1
fi

aws ecs wait tasks-stopped \
  --region "$REGION" \
  --cluster "$CLUSTER" \
  --tasks "$TASK_ARN"

EXIT_CODE="$(
  aws ecs describe-tasks \
    --region "$REGION" \
    --cluster "$CLUSTER" \
    --tasks "$TASK_ARN" \
    --query 'tasks[0].containers[0].exitCode' \
    --output text
)"

if [[ "$EXIT_CODE" != "0" ]]; then
  echo "Migration failed. Application deployment stopped." >&2
  aws ecs describe-tasks \
    --region "$REGION" \
    --cluster "$CLUSTER" \
    --tasks "$TASK_ARN"
  exit 1
fi

declare -A SERVICES=(
  ["$API_SERVICE"]="$API_FAMILY"
  ["$TRYON_SERVICE"]="$TRYON_FAMILY"
  ["$INGEST_SERVICE"]="$INGEST_FAMILY"
  ["$BEAT_SERVICE"]="$BEAT_FAMILY"
)

declare -A CONTAINERS=(
  ["$API_SERVICE"]="api"
  ["$TRYON_SERVICE"]="worker"
  ["$INGEST_SERVICE"]="worker"
  ["$BEAT_SERVICE"]="beat"
)

for service in "${!SERVICES[@]}"; do
  family="${SERVICES[$service]}"
  container="${CONTAINERS[$service]}"
  task_definition="$(
    register_task_definition "$family" "$container"
  )"
  aws ecs update-service \
    --region "$REGION" \
    --cluster "$CLUSTER" \
    --service "$service" \
    --task-definition "$task_definition" \
    --deployment-configuration \
    "deploymentCircuitBreaker={enable=true,rollback=true},minimumHealthyPercent=100,maximumPercent=200" \
    >/dev/null
done

aws ecs wait services-stable \
  --region "$REGION" \
  --cluster "$CLUSTER" \
  --services \
  "$API_SERVICE" \
  "$TRYON_SERVICE" \
  "$INGEST_SERVICE" \
  "$BEAT_SERVICE"

curl --fail --silent --show-error \
  "${API_BASE}/healthz/live"
curl --fail --silent --show-error \
  "${API_BASE}/healthz/ready"

echo "Promotion completed for ${ENVIRONMENT}."
echo "Image: ${IMAGE_URI}"
