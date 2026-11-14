# Redis Backup and Restore Policy

> **Disaster recovery protocol. Pre-pilot status maintained per AGENTS.md.**

---

## 1. Backup Strategy

While Redis operates primarily as an in-memory cache and task queue, automated snapshots ensure recovery of unconsumed queue tasks and state in disaster scenarios.

### Snapshot Policies by Environment:

| Environment | Snapshot Frequency | Retention Limit | Daily Snapshot Window |
| :--- | :--- | :--- | :--- |
| **Development** | None (Disabled) | 0 Days | N/A |
| **Staging** | Automated Daily | 1 Day | 03:00 - 04:00 UTC |
| **Production** | Automated Daily | 7 Days | 02:00 - 03:00 UTC |

---

## 2. Manual Backup Creation

Before significant infrastructure changes, migrations, or software upgrades, create an ad-hoc snapshot via AWS CLI:

```bash
aws elasticache create-snapshot \
  --replication-group-id fashx-redis-prod \
  --snapshot-name "fashx-redis-prod-manual-$(date +%Y%m%d%H%M%S)" \
  --region ap-south-1
```

---

## 3. Restore Protocol

To restore an ElastiCache Redis cluster from a snapshot:

1. Identify the target snapshot name:
   ```bash
   aws elasticache describe-snapshots \
     --replication-group-id fashx-redis-prod \
     --region ap-south-1 \
     --query 'Snapshots[*].{Name:SnapshotName,Status:SnapshotStatus,Date:NodeSnapshots[0].SnapshotCreateTime}' \
     --output table
   ```
2. Restore into a new replication group:
   ```bash
   aws elasticache create-replication-group \
     --replication-group-id fashx-redis-prod-restored \
     --replication-group-description "Restored Production Redis" \
     --snapshot-name "<SELECTED_SNAPSHOT_NAME>" \
     --node-type cache.r6g.large \
     --num-cache-clusters 3 \
     --cache-subnet-group-name fashx-redis-subnet-group \
     --security-group-ids sg-0123456789abcdef0 \
     --region ap-south-1
   ```
3. Update DNS CNAME or AWS Secrets Manager `REDIS_URL` pointing application traffic to the restored cluster endpoint.
