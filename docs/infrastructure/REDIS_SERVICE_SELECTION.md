# Redis & In-Memory Service Selection Decision Record

> **Engineering decision record. Pre-pilot status maintained per AGENTS.md.**

---

## 1. Context & Business Drivers

FashXStudio requires a high-performance in-memory key-value data store to support:
1. Celery distributed task queue broker and results caching.
2. Low-latency rate limiting sliding-window counters for API DDOS protection.
3. Fast session state management and transient JWKS key caching.
4. Future real-time garment recommendation lookups.

## 2. Alternatives Evaluated

| Evaluation Criteria | AWS ElastiCache for Redis 7.1 | AWS MemoryDB for Redis | Self-Hosted Redis (EC2 / Docker) |
| :--- | :--- | :--- | :--- |
| **Engine Compatibility** | 100% Redis 7.1 API | Redis 7.1 API | Redis 7.2 Open Source / Valkey |
| **Persistence Model** | In-memory + AOF + Periodic Snapshots | Multi-AZ Transaction Log (ACID) | Disk persistence (RDB/AOF on EBS) |
| **Write Latency** | Sub-millisecond (< 1 ms) | Low single-digit ms (write-through) | Sub-millisecond (< 1 ms) |
| **Read Latency** | Microseconds (< 500 us) | Microseconds (< 500 us) | Microseconds (< 500 us) |
| **High Availability** | Multi-AZ Automatic Failover (< 60s) | Multi-AZ Automatic Failover | Manual Sentinel / Pacemaker setup |
| **Security & Compliance** | In-transit TLS, KMS encryption, IAM / AUTH | In-transit TLS, KMS encryption | Requires custom TLS certificates & keys |
| **Operational Burden** | Fully managed (zero patching downtime) | Fully managed | High (patching, backup scripts, disk fills) |
| **Relative Cost** | Baseline ($) | High ($$$$ - transactional log premium)| Low ($ - instance cost only) |

---

## 3. Decision: AWS ElastiCache for Redis 7.1

**Selected Service**: **Amazon ElastiCache for Redis 7.1** in `ap-south-1` (Mumbai).

### Rationale:
1. **Sub-millisecond Performance**: Celery queue dispatch and API rate-limiting require sub-millisecond roundtrips that ElastiCache delivers consistently.
2. **Cost Efficiency**: MemoryDB's distributed multi-AZ transaction log creates unnecessary billing overhead for transient queues and cache data where snapshot-based durability is sufficient.
3. **Operational Simplicity**: Self-hosted Redis on EC2 introduces significant maintenance liabilities (failover management, manual point-in-time recovery, certificate renewal).
4. **Data Localization**: Fully hosted within AWS Mumbai data centers, complying with Indian DPDP data sovereignty guidelines.
