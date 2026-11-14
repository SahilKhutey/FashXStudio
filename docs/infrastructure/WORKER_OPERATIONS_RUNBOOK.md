# FashXStudio — Worker Operations & Troubleshooting Runbook (Phase 03.3)

## 1. Metric Monitoring & Alarms
The following CloudWatch metrics and alarms are configured for the ElastiCache cluster and worker ECS services:

| Metric / Alarm | Threshold | Evaluation Period | Severity | Action |
| :--- | :--- | :--- | :--- | :--- |
| **`EngineCPUUtilization`** | >= 75% | 3 consecutive periods of 1m | High | Scale up node type or check for hot keys / heavy loops. |
| **`DatabaseMemoryUsagePercentage`** | >= 75% | 2 consecutive periods of 5m | High | Check key eviction rate; verify Celery result backend is disabled. |
| **`CurrConnections`** | >= 1,000 | 1 period of 5m | Warning | Check for connection pooling leaks in worker processes. |
| **Dead-Letter Backlog** | > 10 pending | 1 period of 5m | Critical | Inspect `worker_dead_letters` table for external provider outage. |

---

## 2. Worker Inspection CLI Commands
Operators with container access can query Celery worker state directly using the Celery CLI:

```bash
# Check worker status and connected nodes
celery -A fashx.workers.app status

# Inspect active tasks currently running
celery -A fashx.workers.app inspect active

# Inspect reserved tasks in worker prefetch buffers
celery -A fashx.workers.app inspect reserved

# Query worker pool statistics and concurrency
celery -A fashx.workers.app inspect stats

# Inspect scheduled beat tasks
celery -A fashx.workers.app inspect scheduled
```

---

## 3. Queue Depth Inspection via Redis CLI
To monitor queue backlog directly on Redis:

```bash
# Check queue length for tryon
LLEN tryon

# Check queue length for ingest
LLEN ingest

# Check queue length for maintenance
LLEN maintenance
```

---

## 4. Incident Response Scenarios

### Scenario A: External VTO Provider Outage (HTTP 503 / 504)
1. **Symptom**: `tryon` tasks exhaust 3 retries; `worker_dead_letters` table accumulates pending records with error `FashnApiError` or `TimeoutError`.
2. **Mitigation**:
   - Check upstream status page.
   - Pause task processing if necessary by scaling down the `fashx-worker-tryon` ECS service to 0.
   - Once provider recovers, scale service back up.
   - Replay pending dead-letter jobs using the replay protocol in `docs/infrastructure/WORKER_DEAD_LETTER_POLICY.md`.

### Scenario B: High Redis Memory Consumption
1. **Symptom**: `DatabaseMemoryUsagePercentage` exceeds 75%.
2. **Mitigation**:
   - Verify result backend is `None`. Run `redis-cli KEYS "celery-task-meta-*"` — count should be 0.
   - Inspect top memory keys: `redis-cli --bigkeys`.
   - Ensure `maxmemory-policy` is set to `volatile-lru`.
