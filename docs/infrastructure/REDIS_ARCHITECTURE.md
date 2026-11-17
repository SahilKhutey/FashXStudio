# FashXStudio — Redis & Background Worker Architecture (Phase 03.3)

## 1. Overview
FashXStudio uses **Amazon ElastiCache for Valkey / Redis** as the asynchronous message broker for background workers orchestrated via Celery. 

The background worker tier manages computationally intensive and asynchronous operations:
- Virtual try-on (VTO) rendering pipeline execution and provider orchestration.
- Catalog merchant product feed ingestion and clearance validation.
- Garment attribute enrichment and visual feature extraction.
- Transactional outbox event relays (erasure tombstones, push notifications).
- Nightly data retention and asset lifecycle purges.

---

## 2. Broker Engine & Technology Selection
- **Engine**: AWS ElastiCache for Valkey 7.2 / Redis OSS 7.1 compatible engine.
- **Protocol**: Redis wire protocol with mandatory TLS 1.2+ encryption in transit (`rediss://`).
- **Authentication**: Redis AUTH token generated cryptographically and managed exclusively in AWS Secrets Manager.
- **Result Backend**: Disabled (`backend=None`, `task_ignore_result=True`). Celery does not persist task results in Redis. All persistent domain state, job outcomes, and audit histories are committed to PostgreSQL.
- **Eviction Policy**: `volatile-lru` with a 300-second idle connection timeout and 60-second TCP keepalive.

---

## 3. Environment Isolation Matrix
Each deployment environment runs an independent ElastiCache replication group with strict network isolation. Non-production environments cannot communicate with production cache clusters.

| Environment | Replication Group ID | Topology | Instance Type | Multi-AZ | Transit Encryption | Auth Token |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Development** | `fashx-redis-dev` | Single Node | `cache.t4g.micro` | No | Required (`rediss://`) | Secrets Manager |
| **Staging** | `fashx-redis-staging` | 1 Primary + 1 Replica | `cache.t4g.small` | No | Required (`rediss://`) | Secrets Manager |
| **Production** | `fashx-redis-prod` | 1 Primary + 2 Replicas | `cache.t4g.medium` | Yes | Required (`rediss://`) | Secrets Manager |

---

## 4. Network and Security Boundary
1. **Private Subnets**: ElastiCache clusters are provisioned strictly inside private data subnets across two or more Availability Zones in the `ap-south-1` (Mumbai) region.
2. **No Public Ingress**: Redis clusters have no public IP addresses, no Internet Gateway routes, and no NAT ingress.
3. **Security Group Ingress**: Port 6379 is restricted solely to the security group assigned to FashXStudio ECS application tasks and Celery worker tasks (`fashx-redis-sg`).
4. **Secret Resolution**: The Celery broker URL is resolved at container startup from AWS Secrets Manager secret `/fashx/${ENVIRONMENT}/redis/url`. Static credentials are not embedded in task definitions, container images, or code.

---

## 5. Architectural Non-Goals
- **No Long-Term Data Storage in Redis**: Redis is treated as an ephemeral message broker. Data loss during failovers is mitigated by PostgreSQL outbox patterns and idempotent task design.
- **No Redis Native Dead-Letter Queues**: Redis does not provide native dead-letter queues. Dead-letter persistence is offloaded to PostgreSQL table `worker_dead_letters`.
- **No Result Caching in Celery**: Task results are never retrieved via `AsyncResult.get()`. Downstream clients poll the database via standard REST endpoints.
