# Managed PostgreSQL Service Selection and Decision Record

## 1. Executive Summary & Selection Decision

For FashXStudio's relational and vector persistence layer, **AWS RDS for PostgreSQL 16** in region **`ap-south-1` (Mumbai, India)** is selected as the primary managed database service.

| Criterion | Selected Architecture |
| :--- | :--- |
| **Engine & Version** | PostgreSQL 16.3+ on Amazon RDS |
| **Vector Search Extension** | `pgvector` v0.7.0+ (supported natively on RDS PG 16) |
| **Deployment Region** | `ap-south-1` (Mumbai, India) |
| **Production Topology** | Multi-AZ with synchronous standby failover (<60s) |
| **Non-Production Topology** | Single-AZ instance hosting isolated `fashx_dev` and `fashx_staging` databases |
| **Connection Pooling** | SQLAlchemy client-side connection pooling + optional Amazon RDS Proxy |
| **Encryption** | At-rest (AWS KMS Customer Managed Key) & in-transit (`rds.force_ssl=1`) |
| **Backup & Recovery** | Automated daily snapshots + continuous WAL archiving (35-day PITR) |

---

## 2. Comparative Evaluation Matrix

| Capability / Requirement | AWS RDS for PostgreSQL | Google Cloud SQL for PG | Neon / Serverless PG | Supabase Managed |
| :--- | :--- | :--- | :--- | :--- |
| **Native `pgvector` Support** | Full native support (`vector` 0.5–0.7+) | Supported on PG 13+ | Supported | Supported natively |
| **India Local Region** | `ap-south-1` (Mumbai), `ap-south-2` (Hyderabad) | `asia-south1` (Mumbai), `asia-south2` (Delhi) | Regional proxy only | AWS `ap-south-1` hosted |
| **Private VPC Peering** | Native AWS VPC security groups | VPC Service Controls | Complex tunnel required | Complex tunnel required |
| **IAM Database Authentication** | Native (eliminates static credentials) | Cloud SQL IAM Auth | Not supported | Not supported |
| **Connection Management** | RDS Proxy (pinning controls, pooling) | Cloud SQL Auth Proxy | Built-in PgBouncer | Built-in Supavisor |
| **Automated Failover** | Multi-AZ synchronous (<60s RTO) | High Availability replica | Ephemeral compute resume | Manual / Pro tier |
| **Point-In-Time Recovery** | Continuous WAL archiving to S3 (1s window) | Continuous WAL (7-day default) | Branching-based | Daily / WAL on Enterprise |
| **FashX Ecosystem Proximity** | Colocated with ECS Fargate & S3 Media | Cross-cloud latency to AWS S3 | Cross-cloud latency | Cross-cloud latency |

---

## 3. Decision Rationale

1. **Ecosystem Colocation**: The compute runtime (ECS Fargate) and private object storage (S3) reside in AWS `ap-south-1`. Placing PostgreSQL in the identical VPC subnets eliminates cross-cloud egress costs, minimizes network roundtrip latency to <2ms for API queries, and enforces zero-trust VPC security groups.
2. **Data Localization & Regulatory Compliance**: Operating within AWS Mumbai (`ap-south-1`) guarantees that Indian shopper demographic profiles, wardrobe preferences, and fit measurements remain within domestic borders, satisfying Digital Personal Data Protection Act (DPDPA) guidelines.
3. **Maturity of pgvector and Extensions**: AWS RDS PostgreSQL 16 natively supports `vector` alongside standard enterprise extensions (`uuid-ossp`, `pg_stat_statements`, `btree_gist`).
4. **Disaster Recovery**: RDS continuous WAL streaming to multi-AZ S3 achieves the <5 minute Recovery Point Objective (RPO) and <60 second Multi-AZ Recovery Time Objective (RTO).
