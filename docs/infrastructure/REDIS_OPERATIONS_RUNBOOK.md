# Redis Operations and Incident Runbook

> **Operational runbook. Pre-pilot status maintained per AGENTS.md.**

---

## 1. CloudWatch Metrics & Alert Thresholds

Monitor the following key ElastiCache CloudWatch metrics:

| Metric | Target / Normal | Warning Threshold | Critical Threshold | Action |
| :--- | :--- | :--- | :--- | :--- |
| **`DatabaseMemoryUsagePercentage`** | < 60% | >= 75% | >= 85% | Trigger cache key audit; scale up instance class |
| **`EngineCPUUtilization`** | < 40% | >= 70% | >= 85% | Inspect slow commands via `SLOWLOG GET` |
| **`ReplicationLag`** | 0 seconds | >= 5 seconds | >= 15 seconds | Check network bandwidth and primary write volume |
| **`CurrConnections`** | 100 - 500 | >= 2,000 | >= 4,000 | Check connection leak in FastAPI pods or workers |
| **`Evictions`** | 0 / min | > 100 / min | > 1,000 / min | High cache thrashing; increase maxmemory |

---

## 2. Common Incident Procedures

### A. High Memory Utilization (> 85%)
1. Identify high memory consuming keys or prefixes:
   ```bash
   redis-cli -u $REDIS_URL --bigkeys
   ```
2. Verify that Celery queues are not accumulating unconsumed tasks:
   ```bash
   python scripts/redis/test_celery_queues.py
   ```
3. If queue depth is normal and cache keys are exhausting memory, trigger vertical node scale-up in Terraform (`cache.r6g.xlarge`).

### B. Node Failover Procedure (Drill or Disaster)
To test automatic failover in staging or production:
```bash
aws elasticache test-failover \
  --replication-group-id fashx-redis-staging \
  --node-group-id 0001 \
  --region ap-south-1
```
Expected behavior:
- Replica is promoted to Primary within 30-60 seconds.
- FastAPI background connection retry reconnects seamlessly.
- Zero task loss for acknowledged tasks.
