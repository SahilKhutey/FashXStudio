# ADR-0008: Production Hosting & Infrastructure Topology

## Status
Accepted

## Date
2026-10-11

## Context
FashX Studio requires a production hosting environment that satisfies:
1. **Regulatory Compliance (India):** CERT-In Directions (June 2022) mandate that ICT system logs be securely maintained within the Indian jurisdiction for 180 days (with a 6-hour incident reporting window). DPDP Rules (notified Nov 2025) require 365-day security and processing log retention. Hosting compute, storage, and telemetry in an Indian cloud region satisfies both without cross-border log latency.
2. **Persistence & Data Isolation:** Managed PostgreSQL 16+ with `pgvector` extension support, automated backups, Point-In-Time Recovery (PITR), and private VPC subnet isolation.
3. **Object Storage:** Private S3 bucket located in India (`ap-south-1`) for user photos, signed capability URLs with 300s TTL, and cryptographic erasure (per ADR-0003).
4. **Operational Overhead:** Manageable by a solo founder without dedicated DevOps staff. Must support containerized API, Celery background workers, and Celery beat scheduler.
5. **Cost Predictability:** Enforceable billing ceiling and alerts ($150-$250/month pilot baseline).

## Options Considered

| Option | Pros | Cons | Decision |
| :--- | :--- | :--- | :--- |
| **AWS Mumbai (`ap-south-1`)** *(Selected)* | Complete regional presence; ECS Fargate eliminates VM patching; RDS Postgres with native `pgvector 0.8.0+`; S3 in Mumbai satisfies user photo data locality; CloudWatch 365-day log retention within India; IAM Task Roles eliminate long-lived storage credentials. | Higher initial IaC setup compared to small PaaS. | **Accepted** |
| **GCP Mumbai (`asia-south1`)** | Cloud Run, Cloud SQL with pgvector, Memorystore. | Background workers requiring persistent queues need Cloud Run Jobs or Compute Engine; Cloud Run WebSocket/long-polling nuances. | Rejected |
| **Small PaaS (Render / Railway / Fly.io)** | Very fast developer experience. | Limited or no Indian region data residency; lacks native VPC private database peering; logs often stream outside India in violation of CERT-In directives. | Rejected |

## Decision
Adopt **AWS Mumbai (`ap-south-1`)** with the following topology:
1. **Compute:** ECS Fargate running hardened Linux containers (`10001:10001` non-root, read-only root filesystem with writable `/tmp`).
   - Service `fashx-api`: Gunicorn + Uvicorn workers behind an Application Load Balancer.
   - Service `fashx-worker`: Celery worker subscribed to `tryon` queue (`concurrency: 3`).
   - Service `fashx-ingest`: Celery worker for catalog ingest and VLM enrichment (`concurrency: 2`).
   - Service `fashx-beat`: Single instance Celery beat scheduler for periodic outbox, price freshness, and retention sweeps.
2. **Database:** RDS PostgreSQL 16 in private subnet with `pgvector` enabled. Automated daily backups with 14-day PITR retention. Single-AZ deployment for the 50-user pilot (accepted risk: restore time RTO ≤ 4h vs multi-AZ cost).
3. **Caching & Broker:** Managed Redis (ElastiCache) in private subnet with in-transit encryption and AUTH token.
4. **Storage:** S3 bucket `fashx-media-prod` located in `ap-south-1`. Bucket policies: block all public ACLs/policies, enforce KMS encryption at rest, deny unencrypted transport (`aws:SecureTransport: false`), and expire `tmp/` objects after 24 hours.
5. **Telemetry:** CloudWatch Logs with 365-day retention policy physically retained in Mumbai.
6. **Environments:** Strict isolation between `staging` (separate VPC, staging Supabase project, test try-on keys with low budget cap, synthetic users only) and `prod`. Staging never stores real user photos.

## Consequences & Accepted Risks
- **Single-AZ Database:** For the 50-user pilot, single-AZ RDS avoids doubling database spend. In the rare event of an AZ disruption, Recovery Time Objective (RTO) is ≤ 4 hours via snapshot restore. Multi-AZ will be provisioned prior to commercial scale.
- **Egress Filtering:** Initial pilot egress restricts outbound traffic to port 443 with application-level SSRF defense (Phase 6). Dedicated egress proxy with DNS hostname allowlisting is deferred to post-pilot.
- **Secrets Management:** Long-lived static credentials eliminated from containers via IAM Task Execution Roles. Remaining third-party API keys stored in AWS Secrets Manager.
