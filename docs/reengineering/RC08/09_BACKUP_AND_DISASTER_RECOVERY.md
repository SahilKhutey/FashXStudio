# RC08 — Backup & Disaster Recovery

## 1. RPO & RTO Targets
- **Recovery Point Objective (RPO)**: ≤ 24 hours (Automated daily full backup + continuous WAL archiving).
- **Recovery Time Objective (RTO)**: ≤ 4 hours (Automated restore scripts to newly provisioned instance).

## 2. Backup Schedule & Retention
- **PostgreSQL**: Daily full snapshot at 02:00 UTC, retained for 30 days. Continuous WAL segments shipped to S3 bucket `fashx-db-wal`.
- **Object Storage**: Bucket versioning enabled on S3 media buckets with 30-day lifecycle rule for noncurrent versions.
- **Secrets & Configuration**: GitOps-tracked infrastructure as code and secure secrets manager versioning.

## 3. Restore Drill Runbook
To verify real recoverability, an isolated restore drill must be executed periodically:
1. Snapshot current staging database.
2. Spin up isolated temporary test database container.
3. Apply snapshot and replay WAL segments up to target point-in-time.
4. Execute `python -m alembic check` to verify schema integrity.
5. Execute smoke query verifying record count and constraint validity.
6. Record elapsed recovery time and data loss delta.
7. Teardown temporary restored container.
