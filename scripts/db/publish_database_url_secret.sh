#!/usr/bin/env bash
set -Eeuo pipefail
set +x

ENVIRONMENT="${1:?Usage: publish_database_url_secret.sh dev|staging|prod}"

case "$ENVIRONMENT" in
  dev)
    DB_ID="fashx-pg-dev"
    DB_NAME="fashx_dev"
    APP_SECRET="fashx/dev/postgres/app"
    URL_SECRET="fashx/dev/postgres/database-url"
    ;;
  staging)
    DB_ID="fashx-pg-staging"
    DB_NAME="fashx_staging"
    APP_SECRET="fashx/staging/postgres/app"
    URL_SECRET="fashx/staging/postgres/database-url"
    ;;
  prod)
    DB_ID="fashx-pg-prod"
    DB_NAME="fashx_prod"
    APP_SECRET="fashx/prod/postgres/app"
    URL_SECRET="fashx/prod/postgres/database-url"
    ;;
  *)
    echo "Invalid environment" >&2
    exit 2
    ;;
esac

REGION="ap-south-1"

HOST="$(
  aws rds describe-db-instances \
    --region "$REGION" \
    --db-instance-identifier "$DB_ID" \
    --query 'DBInstances[0].Endpoint.Address' \
    --output text
)"

APP_JSON="$(
  aws secretsmanager get-secret-value \
    --region "$REGION" \
    --secret-id "$APP_SECRET" \
    --query SecretString \
    --output text
)"

USER_NAME="$(jq -r '.username' <<< "$APP_JSON")"
PASSWORD="$(jq -r '.password' <<< "$APP_JSON")"

DATABASE_URL="postgresql+asyncpg://${USER_NAME}:${PASSWORD}@${HOST}:5432/${DB_NAME}"

if aws secretsmanager describe-secret \
  --region "$REGION" \
  --secret-id "$URL_SECRET" >/dev/null 2>&1; then
  aws secretsmanager put-secret-value \
    --region "$REGION" \
    --secret-id "$URL_SECRET" \
    --secret-string "$DATABASE_URL" >/dev/null
else
  aws secretsmanager create-secret \
    --region "$REGION" \
    --name "$URL_SECRET" \
    --secret-string "$DATABASE_URL" >/dev/null
fi

unset PASSWORD DATABASE_URL APP_JSON
echo "Published database URL secret for ${ENVIRONMENT}."
