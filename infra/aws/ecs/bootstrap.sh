#!/usr/bin/env bash
set -Eeuo pipefail

REGION="ap-south-1"

for ENV in dev staging prod; do
  CLUSTER="fashx-${ENV}"
  if ! aws ecs describe-clusters \
    --region "$REGION" \
    --clusters "$CLUSTER" \
    --query 'clusters[0].status' \
    --output text 2>/dev/null | grep -q ACTIVE; then
    aws ecs create-cluster \
      --region "$REGION" \
      --cluster-name "$CLUSTER" \
      --settings name=containerInsights,value=enabled \
      >/dev/null
  fi

  for SERVICE in api tryon ingest beat migration; do
    LOG_GROUP="/fashx/${ENV}/${SERVICE}"
    aws logs create-log-group \
      --region "$REGION" \
      --log-group-name "$LOG_GROUP" \
      2>/dev/null || true
    aws logs put-retention-policy \
      --region "$REGION" \
      --log-group-name "$LOG_GROUP" \
      --retention-in-days 30
  done
done

echo "ECS clusters and CloudWatch log groups bootstrap completed."
