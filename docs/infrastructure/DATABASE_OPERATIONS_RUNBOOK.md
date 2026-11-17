# PostgreSQL Database Operations & Maintenance Runbook

## 1. Routine Maintenance and Autovacuum Policy

PostgreSQL autovacuum is managed automatically by Amazon RDS with tuned parameters in `fashx-postgres16-params`:

```text
autovacuum = on
autovacuum_vacuum_scale_factor = 0.05
autovacuum_analyze_scale_factor = 0.02
autovacuum_vacuum_cost_limit = 1000
```

### Manual Maintenance Queries (Low-Traffic Maintenance Window)
```sql
-- Analyze table statistics after major bulk catalog ingestion
ANALYZE catalog_garments;
ANALYZE garment_enrichments;

-- Check table bloat and dead tuple counts
SELECT
    relname,
    n_live_tup,
    n_dead_tup,
    round((n_dead_tup::numeric / nullif(n_live_tup + n_dead_tup, 0)::numeric) * 100, 2) AS dead_pct,
    last_vacuum,
    last_autovacuum
FROM pg_stat_user_tables
ORDER BY n_dead_tup DESC;
```

---

## 2. Emergency Operational Procedures

### A. Diagnosing and Terminating Blocked / Long-Running Queries
If an unindexed query or deadlock blocks application traffic:

```sql
-- 1. Identify active queries running longer than 30 seconds
SELECT
    pid,
    usename,
    client_addr,
    now() - query_start AS duration,
    wait_event_type,
    wait_event,
    left(query, 200) AS query_preview
FROM pg_stat_activity
WHERE state != 'idle'
  AND (now() - query_start) > interval '30 seconds'
ORDER BY duration DESC;

-- 2. Gracefully cancel the long-running statement
SELECT pg_cancel_backend(<PID>);

-- 3. If unresponsive, forcibly terminate the backend connection
SELECT pg_terminate_backend(<PID>);
```

### B. Connection Saturation Emergency (Evicting Idle Connections)
If the connection pool approaches 95% capacity due to leaked connections:

```sql
-- Terminate all connections from 'idle in transaction' state older than 5 minutes
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE state = 'idle in transaction'
  AND (now() - state_change) > interval '5 minutes';
```

---

## 3. High Availability Failover Procedure

To trigger a manual failover test or remediate an unhealthy primary host:

```bash
aws rds reboot-db-instance \
  --db-instance-identifier fashx-pg-prod \
  --force-failover \
  --region ap-south-1
```

- Expected failover duration: **30–50 seconds**.
- The standby instance in the secondary AZ is promoted to primary.
- The CNAME endpoint automatically updates via Route 53 DNS with 5-second TTL.
- SQLAlchemy with `pool_pre_ping=True` drops broken connections and reconnects to the newly promoted primary without restarting application containers.
