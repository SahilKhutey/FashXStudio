#!/usr/bin/env bash
# ==============================================================================
# FashXStudio ECS Rollback Script
# ==============================================================================
set -euo pipefail

ENVIRONMENT="${1:-staging}"
STATE_FILE="${2:-/tmp/deploy-state/rollback_state.json}"

echo "=========================================================="
echo " Initiating Rollback for Environment: $ENVIRONMENT"
echo " State File: $STATE_FILE"
echo "=========================================================="

bash scripts/release/rollback_ecs.sh "$ENVIRONMENT" "$STATE_FILE"
