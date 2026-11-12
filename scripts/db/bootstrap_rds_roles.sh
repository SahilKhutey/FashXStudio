#!/usr/bin/env bash
set -Eeuo pipefail
set +x

# ==============================================================================
# FashXStudio: AWS RDS PostgreSQL Role & Secrets Bootstrap
# Usage: ./bootstrap_rds_roles.sh <dev|staging|prod>
# ==============================================================================

ENVIRONMENT="${1:?Usage: bootstrap_rds_roles.sh dev|staging|prod}"

case "$ENVIRONMENT" in
  dev)
    DB_ID="fashx-pg-dev"
    DB_NAME="fashx_dev"
    APP_ROLE="fashx_dev_app"
    MIGRATOR_ROLE="fashx_dev_migrator"
    ;;
  staging)
    DB_ID="fashx-pg-staging"
    DB_NAME="fashx_staging"
    APP_ROLE="fashx_staging_app"
    MIGRATOR_ROLE="fashx_staging_migrator"
    ;;
  prod)
    DB_ID="fashx-pg-prod"
    DB_NAME="fashx_prod"
    APP_ROLE="fashx_prod_app"
    MIGRATOR_ROLE="fashx_prod_migrator"
    ;;
  *)
    echo "Invalid environment: $ENVIRONMENT (allowed: dev, staging, prod)" >&2
    exit 2
    ;;
esac

REGION="${AWS_REGION:-ap-south-1}"
CA_FILE="${AWS_RDS_CA_FILE:-/tmp/aws-rds-global-bundle.pem}"

mkdir -p "$(dirname "$CA_FILE")"

if [[ ! -s "$CA_FILE" ]]; then
  echo "Downloading AWS RDS global root CA bundle..."
  curl -fsSL \
    https://truststore.pki.rds.amazonaws.com/global/global-bundle.pem \
    -o "$CA_FILE"
fi

DB_ENDPOINT="$(
  aws rds describe-db-instances \
    --region "$REGION" \
    --db-instance-identifier "$DB_ID" \
    --query 'DBInstances[0].Endpoint.Address' \
    --output text
)"

MASTER_SECRET_ARN="$(
  aws rds describe-db-instances \
    --region "$REGION" \
    --db-instance-identifier "$DB_ID" \
    --query 'DBInstances[0].MasterUserSecret.SecretArn' \
    --output text
)"

if [[ "$MASTER_SECRET_ARN" == "None" || -z "$MASTER_SECRET_ARN" ]]; then
  echo "ERROR: RDS master secret is unavailable for $DB_ID." >&2
  exit 1
fi

MASTER_JSON="$(
  aws secretsmanager get-secret-value \
    --region "$REGION" \
    --secret-id "$MASTER_SECRET_ARN" \
    --query SecretString \
    --output text
)"

MASTER_USER="$(jq -r '.username' <<< "$MASTER_JSON")"
MASTER_PASSWORD="$(jq -r '.password' <<< "$MASTER_JSON")"

create_app_secret() {
  local role="$1"
  local secret_name="$2"

  if aws secretsmanager describe-secret \
      --region "$REGION" \
      --secret-id "$secret_name" >/dev/null 2>&1; then
    echo "Secret already exists: $secret_name"
    return
  fi

  local template
  template="$(
    jq -n \
      --arg username "$role" \
      --arg host "$DB_ENDPOINT" \
      --arg dbname "$DB_NAME" \
      '{
        username: $username,
        host: $host,
        port: 5432,
        dbname: $dbname,
        sslmode: "verify-full"
      }'
  )"

  local generation_config
  generation_config="$(
    jq -n \
      --arg template "$template" \
      '{
        SecretStringTemplate: $template,
        GenerateStringKey: "password",
        PasswordLength: 40,
        ExcludePunctuation: true
      }'
  )"

  aws secretsmanager create-secret \
    --region "$REGION" \
    --name "$secret_name" \
    --description "FashX ${ENVIRONMENT} PostgreSQL ${role} credential" \
    --generate-secret-string "$generation_config" \
    >/dev/null

  echo "Created secret: $secret_name"
}

APP_SECRET_NAME="fashx/${ENVIRONMENT}/postgres/app"
MIGRATOR_SECRET_NAME="fashx/${ENVIRONMENT}/postgres/migrator"

create_app_secret "$APP_ROLE" "$APP_SECRET_NAME"
create_app_secret "$MIGRATOR_ROLE" "$MIGRATOR_SECRET_NAME"

APP_JSON="$(
  aws secretsmanager get-secret-value \
    --region "$REGION" \
    --secret-id "$APP_SECRET_NAME" \
    --query SecretString \
    --output text
)"

MIGRATOR_JSON="$(
  aws secretsmanager get-secret-value \
    --region "$REGION" \
    --secret-id "$MIGRATOR_SECRET_NAME" \
    --query SecretString \
    --output text
)"

APP_PASSWORD="$(jq -r '.password' <<< "$APP_JSON")"
MIGRATOR_PASSWORD="$(jq -r '.password' <<< "$MIGRATOR_JSON")"

echo "Creating/updating PostgreSQL roles for $ENVIRONMENT..."

PGPASSWORD="$MASTER_PASSWORD" psql \
  "host=${DB_ENDPOINT} port=5432 dbname=${DB_NAME} user=${MASTER_USER} sslmode=verify-full sslrootcert=${CA_FILE}" \
  -v ON_ERROR_STOP=1 \
  -v app_role="$APP_ROLE" \
  -v app_password="$APP_PASSWORD" \
  -v migration_role="$MIGRATOR_ROLE" \
  -v migration_password="$MIGRATOR_PASSWORD" \
  <<'SQL'

SELECT format(
  'CREATE ROLE %I LOGIN PASSWORD %L NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION',
  :'app_role',
  :'app_password'
)
WHERE NOT EXISTS (
  SELECT 1 FROM pg_roles WHERE rolname = :'app_role'
)
\gexec

SELECT format(
  'ALTER ROLE %I LOGIN PASSWORD %L NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION',
  :'app_role',
  :'app_password'
)
WHERE EXISTS (
  SELECT 1 FROM pg_roles WHERE rolname = :'app_role'
)
\gexec

SELECT format(
  'CREATE ROLE %I LOGIN PASSWORD %L NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION',
  :'migration_role',
  :'migration_password'
)
WHERE NOT EXISTS (
  SELECT 1 FROM pg_roles WHERE rolname = :'migration_role'
)
\gexec

SELECT format(
  'ALTER ROLE %I LOGIN PASSWORD %L NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION',
  :'migration_role',
  :'migration_password'
)
WHERE EXISTS (
  SELECT 1 FROM pg_roles WHERE rolname = :'migration_role'
)
\gexec

SELECT format(
  'GRANT CONNECT ON DATABASE %I TO %I',
  current_database(),
  :'app_role'
)
\gexec

SELECT format(
  'GRANT CONNECT ON DATABASE %I TO %I',
  current_database(),
  :'migration_role'
)
\gexec

REVOKE CREATE ON SCHEMA public FROM PUBLIC;

GRANT USAGE ON SCHEMA public TO :"app_role";
GRANT USAGE, CREATE ON SCHEMA public TO :"migration_role";

GRANT SELECT, INSERT, UPDATE, DELETE
ON ALL TABLES IN SCHEMA public
TO :"app_role";

GRANT USAGE, SELECT, UPDATE
ON ALL SEQUENCES IN SCHEMA public
TO :"app_role";

ALTER DEFAULT PRIVILEGES
FOR ROLE :"migration_role"
IN SCHEMA public
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES
TO :"app_role";

ALTER DEFAULT PRIVILEGES
FOR ROLE :"migration_role"
IN SCHEMA public
GRANT USAGE, SELECT, UPDATE ON SEQUENCES
TO :"app_role";

SQL

unset MASTER_PASSWORD APP_PASSWORD MIGRATOR_PASSWORD

echo "Database role bootstrap completed for $ENVIRONMENT."
echo "Application secret: $APP_SECRET_NAME"
echo "Migration secret: $MIGRATOR_SECRET_NAME"
