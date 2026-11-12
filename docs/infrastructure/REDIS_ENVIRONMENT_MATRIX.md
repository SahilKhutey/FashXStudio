# Redis Environment Configuration Matrix

> **Technical matrix. Pre-pilot status maintained per AGENTS.md.**

---

## 1. Technical Environment Matrix

| Dimension | Local (`local`) | Development (`development`) | Staging (`staging`) | Production (`production`) |
| :--- | :--- | :--- | :--- | :--- |
| **Hosting Model** | Local Docker Compose | AWS ElastiCache | AWS ElastiCache | AWS ElastiCache |
| **Cluster Identifier** | `fashx-redis-local` | `fashx-redis-dev` | `fashx-redis-staging` | `fashx-redis-prod` |
| **AWS Region** | Localhost | `ap-south-1` | `ap-south-1` | `ap-south-1` |
| **Node Instance Type** | Container | `cache.t4g.micro` | `cache.t4g.small` | `cache.r6g.large` |
| **Node Count** | 1 Container | 1 Node | 2 Nodes (1 Primary + 1 Replica) | 3 Nodes (1 Primary + 2 Replicas) |
| **Multi-AZ enabled** | False | False | False | True (3 AZs: `a`, `b`, `c`) |
| **Auto Failover** | False | False | True | True |
| **Connection Scheme** | `redis://` | `redis://` | `rediss://` (TLS) | `rediss://` (TLS) |
| **In-Transit Encryption** | False | False | True | True |
| **At-Rest Encryption** | False | False | True (AWS-managed) | True (KMS CMK) |
| **Auth Mechanism** | None | None | Secrets Manager AUTH Token | Secrets Manager AUTH Token |
| **Memory Allocation** | Host bound | 500 MB | 1.37 GB | 13.07 GB |
| **Maxmemory Policy** | `volatile-lru` | `volatile-lru` | `volatile-lru` | `volatile-lru` |
| **Celery Tasks** | Eager or Docker Redis | Celery Worker | Celery Worker | Clustered Celery Autoscaling |
| **Daily Snapshots** | None | None | 1-Day Retention | 7-Day Retention (02:00-03:00 UTC) |
| **Maintenance Window** | N/A | Sun 04:30-05:30 UTC | Sun 04:00-05:00 UTC | Sun 03:30-04:30 UTC |

---

## 2. Invariant Rules Across Environments

1. **Production TLS Invariant**: `REDIS_URL` in production MUST start with `rediss://`. Unencrypted `redis://` connections fail release config validation.
2. **Credential Segregation**: Production Redis auth tokens are generated randomly in AWS Secrets Manager and never reused across staging or dev.
3. **Queue Independence**: Task routing is strictly enforced so that staging workers cannot poll or consume production tasks, and dev environments operate on isolated broker instances.
