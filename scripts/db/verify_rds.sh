#!/usr/bin/env bash
set -Eeuo pipefail

# ==============================================================================
# FashXStudio: AWS RDS Instance Status Inspector
# ==============================================================================

REGION="${AWS_REGION:-ap-south-1}"

echo "=================================================================="
echo "FASHXSTUDIO AWS RDS POSTGRESQL INSTANCE AUDIT ($REGION)"
echo "=================================================================="

for DB_ID in fashx-pg-dev fashx-pg-staging fashx-pg-prod; do
  echo "Inspecting instance: ${DB_ID}..."

  aws rds describe-db-instances \
    --region "$REGION" \
    --db-instance-identifier "$DB_ID" \
    --query 'DBInstances[0].{
      Identifier:DBInstanceIdentifier,
      Status:DBInstanceStatus,
      EngineVersion:EngineVersion,
      Class:DBInstanceClass,
      PublicAccess:PubliclyAccessible,
      Encrypted:StorageEncrypted,
      BackupRetentionDays:BackupRetentionPeriod,
      MultiAZ:MultiAZ,
      DeletionProtection:DeletionProtection,
      Endpoint:Endpoint.Address
    }' \
    --output table || echo "Notice: Instance ${DB_ID} is unprovisioned or unreachable in $REGION."
done
