# Redis Memory Allocation and Eviction Policy

> **Capacity planning & memory policy. Pre-pilot status maintained per AGENTS.md.**

---

## 1. Memory Sizing & Allocation Strategy

Redis memory allocation is shared between transient session caching, rate limiting counters, and Celery task broker queues:

| Workload Category | Sizing Allocation | Key TTL Strategy |
| :--- | :--- | :--- |
| **Celery Task Queues (`tryon`, `ingest`, `maintenance`)** | 40% of available memory | Unacknowledged tasks persisted until processed |
| **Celery Result Backend** | 20% of available memory | TTL: 3600 seconds (1 hour auto-expiration) |
| **API Rate Limiter Sliding Windows** | 15% of available memory | TTL: 60 - 3600 seconds (window duration) |
| **JWKS / Auth Session Caching** | 5% of available memory | TTL: 300 - 900 seconds (5 - 15 minutes) |
| **Redis System Overhead & Replication Buffer** | 20% reserved memory | Reserved memory for AOF rewrites and replication backlog |

---

## 2. Maxmemory Eviction Policy: `volatile-lru`

The parameter group `fashx-redis7-params` sets:
```text
maxmemory-policy = volatile-lru
```

### Justification:
- **`volatile-lru`** evicts the least recently used keys among those that have an **explicit expiration (TTL)** set.
- **Queue Protection**: Celery task queue keys (`tryon`, `ingest`, `maintenance` lists) do **NOT** have TTLs set while waiting in queue. `volatile-lru` guarantees that pending user tryon tasks or catalog ingestion jobs will **NEVER** be evicted to free memory for expired rate limits or cache entries.
- If all memory is exhausted and no keys with TTL can be evicted, Redis returns an `OOM command not allowed` error, alerting the infrastructure team rather than silently dropping shopper try-on tasks.

---

## 3. Reserved Memory Sizing

AWS ElastiCache parameter `reserved-memory-percent` is set to `25%` on production (`cache.r6g.large`).
This ensures adequate memory buffer during:
- Automatic failover synchronizations.
- Redis background snapshotting (`BGSAVE`) without triggering Linux kernel out-of-memory killing.
