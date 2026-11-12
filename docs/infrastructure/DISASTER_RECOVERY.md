# Disaster Recovery and Business Continuity Plan

## 1. Disaster Recovery Scenarios & Response Matrix

FashXStudio defines clear protocols for three distinct disaster severity levels:

| Scenario | Impact Severity | Architecture Response | Expected RTO | Expected RPO |
| :--- | :--- | :--- | :--- | :--- |
| **Availability Zone (AZ) Outage** | Low / Automated | Multi-AZ RDS failover; ECS tasks distributed across 3 private subnets | < 60 seconds | 0 data loss |
| **Data Corruption / Drop Table** | Medium | Point-in-time recovery (PITR) to timestamp immediately preceding corruption | < 30 minutes | < 5 minutes |
| **Full AWS Region Outage** | Critical | Cold restore from cross-region S3 backups and RDS snapshots into secondary region | < 4 hours | < 24 hours |

---

## 2. Multi-AZ High Availability Architecture

In the primary production region (`ap-south-1` / Mumbai):
1. **Compute (ECS Fargate)**: Tasks are scheduled across three Availability Zones (`ap-south-1a`, `ap-south-1b`, `ap-south-1c`). Loss of a single AZ triggers automated container task rescheduling on healthy nodes.
2. **Database (Amazon RDS)**: PostgreSQL operates in Multi-AZ configuration with synchronous physical replication to a standby instance in an alternate AZ. Automatic failover completes in under 60 seconds with zero manual intervention.
3. **Storage (Amazon S3)**: S3 automatically replicates objects across a minimum of three distinct physical AZs.

---

## 3. Backup Cadence and Lifecycle

### 3.1 Relational Database (PostgreSQL)
- **Continuous Write-Ahead Log (WAL) Archiving**: Transactions are streamed continuously to S3-backed storage, providing Point-In-Time Recovery with granularity down to the second.
- **Daily Full Snapshots**: Automated RDS snapshots taken daily at 02:00 UTC and retained for 35 days.
- **Pre-Migration Manual Snapshots**: Generated immediately prior to every production database migration.

### 3.2 Object Storage (Private S3 Media)
- **S3 Bucket Versioning**: Enabled on `fashx-prod-media-private` to prevent accidental overwrites or malicious deletions.
- **MFA Delete**: Enforced on the root KMS key and bucket configuration.

---

## 4. Restore Rehearsal Protocol

Backup systems that are never tested inevitably fail during real emergencies. FashXStudio requires a mandatory monthly restore rehearsal:

### Monthly Rehearsal Steps:
1. **Provision Temporary Sandbox Database**:
   ```bash
   aws rds restore-db-instance-to-point-in-time \
     --source-db-instance-identifier fashx-prod-postgres \
     --target-db-instance-identifier fashx-rehearsal-temp-db \
     --restore-time $(date -u -v-2H +"%Y-%m-%dT%H:%M:%SZ") \
     --db-subnet-group-name fashx-private-db-subnet
   ```
2. **Validate Schema & Integrity**: Run Alembic check and integrity verification queries against `fashx-rehearsal-temp-db`.
3. **Verify Row Counts & Table Health**: Verify table record counts match production metrics at the restore timestamp.
4. **Decommission Sandbox**: Destroy `fashx-rehearsal-temp-db` immediately after logging verification evidence.

---

## 5. Disaster Recovery Governance Ledger

| Property | Specification / Requirement |
| :--- | :--- |
| **Backup Schedule** | Daily full snapshots at 02:00 UTC + Continuous WAL archiving |
| **Backup Retention** | 35 days continuous PITR; monthly compliance snapshots retained 1 year |
| **Encryption** | AWS KMS Customer Managed Key (`aws/rds` and `aws/s3`) with automatic rotation |
| **PITR Granularity** | 1-second point-in-time recovery window |
| **Restore Owner** | Infrastructure Lead & Human Founder |
| **Recovery Environment** | Temporary isolated VPC subnet (`fashx-rehearsal-temp`) |
| **Data Integrity Check** | Alembic check + row count parity + checksum verification |
| **Restore Rehearsal Frequency** | Monthly scheduled drill |
| **Current Rehearsal Status** | Planned (Unprovisioned cloud infrastructure) |
