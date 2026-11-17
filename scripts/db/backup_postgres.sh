#!/usr/bin/env bash
set -Eeuo pipefail

# ==============================================================================
# FashXStudio: PostgreSQL Database Logical Backup Script
# Performs consistent custom-format pg_dump with integrity hashing
# ==============================================================================

: "${DATABASE_URL:?DATABASE_URL must be set via environment or secret manager}"
: "${BACKUP_DIR:=./backups}"

mkdir -p "$BACKUP_DIR"

timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
backup_file="${BACKUP_DIR}/fashx-${timestamp}.dump"

echo "Starting PostgreSQL logical backup..."

pg_dump \
  --dbname="$DATABASE_URL" \
  --format=custom \
  --no-owner \
  --no-acl \
  --file="$backup_file"

test -s "$backup_file"

# Validate backup file integrity with pg_restore table of contents listing
pg_restore --list "$backup_file" >/dev/null

echo "Backup completed: $backup_file"
sha256sum "$backup_file" > "${backup_file}.sha256"

echo "Backup validation and SHA256 checksum generated successfully."
