# Database Backup Policy and Retention Schedule

## 1. Multi-Tier Backup Architecture

FashXStudio deploys a dual-tier backup strategy to ensure zero data loss and compliance with enterprise audit requirements:

1. **Continuous Write-Ahead Log (WAL) Archiving (Physical Tier)**:
   - All transactions are streamed continuously to redundant S3 storage in `ap-south-1`.
   - Provides granular Point-In-Time Recovery (PITR) down to the exact second.
2. **Automated Daily Snapshots (Storage Tier)**:
   - Full instance storage volume snapshots executed daily during low-traffic maintenance windows (01:30–02:30 UTC).
   - Tagged automatically and encrypted with AWS KMS.
3. **Pre-Migration Manual Snapshots (Operational Tier)**:
   - Generated immediately prior to deploying any Alembic database migration in Production or Staging.
4. **Logical Dump Exports (Disaster Recovery Sandbox Tier)**:
   - Custom-format logical exports created via [`scripts/db/backup_postgres.sh`](file:///c:/Users/ASUS/Documents/FashXStudio/scripts/db/backup_postgres.sh) for quarterly restoration drills into temporary sandboxes.

---

## 2. Retention Schedule by Environment

| Environment | Daily Snapshot Retention | Continuous PITR Window | Monthly Long-Term Archive | Encryption Key |
| :--- | :--- | :--- | :--- | :--- |
| **Development** | 7 days | Not active | None | AWS Default RDS KMS |
| **Staging** | 7 days | 7 days | None | AWS Default RDS KMS |
| **Production** | 35 days | 35 days | 12 months (Glacier) | Customer Managed KMS Key (`fashx-rds-key`) |

---

## 3. Operational Responsibilities and Alerts

- **Backup Automation**: Managed entirely by AWS RDS automated backup service.
- **Alerting**: CloudWatch alarm triggered on `EventCategory: backup` with event `RDS-EVENT-0003` (Backup failed), routing high-priority alerts to the engineering on-call channel.
- **Access Restrictions**: Restoring a database snapshot requires explicit IAM permissions (`rds:RestoreDBInstanceFromDBSnapshot`, `rds:RestoreDBInstanceToPointInTime`) restricted strictly to the Infrastructure Lead.
