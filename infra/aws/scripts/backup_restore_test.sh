#!/usr/bin/env bash
# ==============================================================================
# FashXStudio Automated RDS Snapshot & Restore Test Drill
# ==============================================================================
set -euo pipefail

ENVIRONMENT="${1:-staging}"
AWS_REGION="${AWS_REGION:-ap-south-1}"
TIMESTAMP="$(date +%Y%m%d%H%M%S)"
SNAPSHOT_ID="fashx-${ENVIRONMENT}-drill-${TIMESTAMP}"
RESTORE_INSTANCE_ID="fashx-${ENVIRONMENT}-restore-test"

echo "=========================================================="
echo " Starting RDS Snapshot & Restore Test Drill"
echo " Primary DB: fashx-pg-${ENVIRONMENT}"
echo " Snapshot ID: $SNAPSHOT_ID"
echo " Restored Test DB: $RESTORE_INSTANCE_ID"
echo "=========================================================="

# 1. Create Manual Snapshot
echo "[1/5] Creating manual DB snapshot..."
START_TIME=$(date +%s)
aws rds create-db-snapshot \
  --db-instance-identifier "fashx-pg-${ENVIRONMENT}" \
  --db-snapshot-identifier "$SNAPSHOT_ID" \
  --region "$AWS_REGION" \
  --output text

echo "Waiting for snapshot $SNAPSHOT_ID to become available..."
aws rds wait db-snapshot-available \
  --db-snapshot-identifier "$SNAPSHOT_ID" \
  --region "$AWS_REGION"
SNAPSHOT_READY_TIME=$(date +%s)
echo "Snapshot available in $((SNAPSHOT_READY_TIME - START_TIME)) seconds."

# 2. Restore to Isolated Validation Instance
echo "[2/5] Restoring snapshot to isolated instance: $RESTORE_INSTANCE_ID..."
RESTORE_START=$(date +%s)
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier "$RESTORE_INSTANCE_ID" \
  --db-snapshot-identifier "$SNAPSHOT_ID" \
  --db-instance-class db.t4g.small \
  --publicly-accessible false \
  --region "$AWS_REGION" \
  --output text

echo "Waiting for restored instance $RESTORE_INSTANCE_ID to become available..."
aws rds wait db-instance-available \
  --db-instance-identifier "$RESTORE_INSTANCE_ID" \
  --region "$AWS_REGION"
RESTORE_END=$(date +%s)
TOTAL_RECOVERY_SECS=$((RESTORE_END - RESTORE_START))
echo "Database successfully restored in $TOTAL_RECOVERY_SECS seconds."

# 3. Retrieve endpoint
RESTORE_ENDPOINT="$(aws rds describe-db-instances --db-instance-identifier "$RESTORE_INSTANCE_ID" --region "$AWS_REGION" --query 'DBInstances[0].Endpoint.Address' --output text)"
echo "[3/5] Restored instance address: $RESTORE_ENDPOINT"

# 4. Teardown restored instance
echo "[4/5] Tearing down temporary restored instance..."
aws rds delete-db-instance \
  --db-instance-identifier "$RESTORE_INSTANCE_ID" \
  --skip-final-snapshot \
  --region "$AWS_REGION" \
  --output text
echo "Restore instance deletion initiated."

# 5. Clean up snapshot if needed
echo "[5/5] Drill completed. Snapshot $SNAPSHOT_ID retained for audit."
echo "=========================================================="
echo " Drill Complete. Total Measured Recovery Time: ${TOTAL_RECOVERY_SECS}s"
echo "=========================================================="
