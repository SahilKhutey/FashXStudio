# Disaster Recovery & Database Restore Runbook

## 1. Objectives & Recovery Targets

- **Recovery Point Objective (RPO)**: **≤ 24 hours** (Automated daily automated RDS snapshots + continuous WAL archiving).
- **Recovery Time Objective (RTO)**: **≤ 4 hours** (Target full service restoration from snapshot).
- **Erasure Invariant (Rule 9.8)**: Restoring an older database backup MUST NEVER resurrect users who exercised their right to erasure between the backup timestamp and the disaster event.

---

## 2. Point-in-Time Recovery Procedure (Step-by-Step)

### Step 1: Restore RDS PostgreSQL Instance from Snapshot
1. Identify the latest daily snapshot:
   ```bash
   aws rds describe-db-snapshots \
     --db-instance-identifier fashx-prod-db \
     --query 'DBSnapshots[-1].DBSnapshotIdentifier' \
     --output text
   ```
2. Restore to a new temporary target instance:
   ```bash
   aws rds restore-db-instance-from-db-snapshot \
     --db-instance-identifier fashx-prod-db-restored \
     --db-snapshot-identifier <SNAPSHOT_ID> \
     --db-instance-class db.t4g.medium \
     --vpc-security-group-ids sg-fashx-db-prod \
     --db-subnet-group-name fashx-prod-db-subnets
   ```
3. Wait until restored instance status reaches `available`.

### Step 2: S3 Point-in-Time Recovery
- Enable S3 Versioning and S3 Object Lock (`COMPLIANCE` / `GOVERNANCE`) on the media bucket.
- To restore deleted objects or rollback S3 bucket to snapshot time:
  ```bash
  python scripts/maintenance/restore_s3_point_in_time.py --bucket fashx-media-prod --timestamp "2026-10-10T00:00:00Z"
  ```

### Step 3: CRITICAL - Replay Erasure Tombstones
To prevent resurrecting accounts that requested deletion after the snapshot was taken:
1. Fetch latest tombstone records from the secondary replica or audit log stream:
2. Execute the tombstone replay script against the restored database:
   ```bash
   python scripts/maintenance/replay_erasure.py \
     --db-url "$RESTORED_DATABASE_URL" \
     --tombstones-file "backups/erasure_tombstones_latest.json"
   ```
3. Verify zero revived accounts:
   ```sql
   SELECT count(*) FROM users WHERE id IN (SELECT user_id FROM erasure_tombstones);
   -- MUST RETURN 0
   ```

### Step 4: Promote Restored Database & Switch Traffic
1. Rename original database instance to `fashx-prod-db-defunct` and rename restored instance to `fashx-prod-db`.
2. Restart ECS service tasks to re-establish database connection pools:
   ```bash
   aws ecs update-service --cluster fashx-prod --service fashx-api --force-new-deployment
   ```
3. Run post-restore verification:
   ```bash
   python scripts/release/smoke.py --base https://api.fashx.studio
   ```
