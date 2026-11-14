# AWS ElastiCache for Redis Architecture Specification

> **Engineering specification. Pre-pilot status maintained per AGENTS.md. Cloud resources documented as planned architecture.**

---

## 1. Executive Summary

This document establishes the architecture for FashXStudio's caching and asynchronous task queue tier using **Amazon ElastiCache for Redis 7.1** in the **`ap-south-1` (Mumbai, India)** region.

Redis serves two critical workloads:
1. **Asynchronous Task Queue Broker (Celery)**: Orchestrates distributed virtual try-on inference (`tryon`), catalog feed ingestion and garment enrichment (`ingest`), and privacy erasure sweeps and retention jobs (`maintenance`).
2. **High-Performance In-Memory Cache & Rate Limiting**: Caches transient session tokens, API rate limiter sliding windows, and JWKS public keys.

---

## 2. Environment Topology

```
+-----------------------------------------------------------------------------------------+
|                                    AWS VPC (ap-south-1)                                 |
|                                                                                         |
|  +-------------------------+  +--------------------------+  +------------------------+  |
|  |       Development       |  |         Staging          |  |       Production       |  |
|  |     fashx-redis-dev     |  |   fashx-redis-staging    |  |    fashx-redis-prod    |  |
|  |                         |  |                          |  |                        |  |
|  |  +-------------------+  |  |  +--------------------+  |  |  +------------------+  |  |
|  |  |   Single Node     |  |  |  |  Primary (Write)   |  |  |  |  Primary (AZ-a)  |  |  |
|  |  | cache.t4g.micro   |  |  |  |  cache.t4g.small   |  |  |  | cache.r6g.large  |  |  |
|  |  +-------------------+  |  |  +---------+----------+  |  |  +--------+---------+  |  |
|  |                         |  |            | Async Repl  |  |           | Sync/Async |  |
|  |  - Cost optimized       |  |  +---------v----------+  |  |  +--------v---------+  |  |
|  |  - No auth token        |  |  |   Replica (Read)   |  |  |  |  Replica (AZ-b)  |  |  |
|  |  - Transit TLS: Off     |  |  |  cache.t4g.small   |  |  |  +--------+---------+  |  |
|  |                         |  |  +--------------------+  |  |           | Replication|  |
|  |                         |  |                          |  |  +--------v---------+  |  |
|  |                         |  |  - Auto-Failover: Yes    |  |  |  Replica (AZ-c)  |  |  |
|  |                         |  |  - Transit TLS: Enforced |  |  +------------------+  |  |
|  |                         |  |  - Auth Token: Secrets   |  |                        |  |
|  |                         |  |                          |  |  - Multi-AZ: Enabled   |  |
|  |                         |  |                          |  |  - Auto-Failover: Yes  |  |
|  |                         |  |                          |  |  - Transit TLS: Enforced| |
|  |                         |  |                          |  |  - At-Rest KMS Encrypt |  |
|  |                         |  |                          |  |  - 7-Day Auto Snapshot |  |
|  +-------------------------+  +--------------------------+  +------------------------+  |
+-----------------------------------------------------------------------------------------+
```

---

## 3. Configuration & Sizing Matrix

| Attribute | Development (`fashx-redis-dev`) | Staging (`fashx-redis-staging`) | Production (`fashx-redis-prod`) |
| :--- | :--- | :--- | :--- |
| **Engine Version** | Redis 7.1 | Redis 7.1 | Redis 7.1 |
| **Node Instance Type** | `cache.t4g.micro` | `cache.t4g.small` | `cache.r6g.large` |
| **vCPU / Memory** | 2 vCPU / 0.5 GiB | 2 vCPU / 1.37 GiB | 2 vCPU / 13.07 GiB |
| **Topology** | 1 Node (Standalone) | 2 Nodes (1 Primary + 1 Replica) | 3 Nodes (1 Primary + 2 Replicas) |
| **Multi-AZ Failover** | Disabled | Auto-Failover (Single AZ) | Enabled (3 Distinct AZs) |
| **In-Transit Encryption** | Disabled (`redis://`) | Enforced (`rediss://`) | Enforced (`rediss://`) |
| **At-Rest Encryption** | Disabled | Enabled (AWS-managed) | Enabled (AWS KMS Customer Key) |
| **Authentication** | None | AUTH Token (Secrets Manager) | AUTH Token (Secrets Manager) |
| **Eviction Policy** | `volatile-lru` | `volatile-lru` | `volatile-lru` |
| **Snapshot Retention** | 0 Days (Disabled) | 1 Day | 7 Days (Daily 02:00-03:00 UTC) |

---

## 4. Workload Segregation & Task Routing

Celery worker tasks are routed to discrete Redis queues to prevent background batch jobs from starving real-time shopper requests:

1. **`tryon` Queue**:
   - Primary task: `fashx.workers.app.process_tryon_job`
   - Workers: Dedicated tryon GPU/worker nodes with `worker_prefetch_multiplier = 1`.
2. **`ingest` Queue**:
   - Primary tasks: `fashx.workers.app.ingest_catalog_feed`, `fashx.workers.app.enrich_garment_task`.
   - Batch ingestion tasks with low priority compared to user tryon operations.
3. **`maintenance` Queue**:
   - Primary tasks: `fashx.workers.app.relay_outbox_events`, `fashx.workers.app.sweep_storage_erasure`, `fashx.workers.app.run_retention_jobs`.
   - Scheduled via Celery Beat for regulatory data pruning and transactional outbox publishing.
