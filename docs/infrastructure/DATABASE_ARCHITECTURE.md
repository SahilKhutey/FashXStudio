# Database Architecture Specification — Managed PostgreSQL 16 (RDS)

## 1. Executive Summary

FashXStudio operates on Amazon Relational Database Service (RDS) for PostgreSQL 16 in the AWS Mumbai region (`ap-south-1`).

To eliminate cross-environment leakage and enforce strict blast-radius isolation, the platform provisions three independent managed database instances across development, staging, and production.

```mermaid
flowchart TD
    subgraph VPC [AWS VPC: ap-south-1 (Mumbai)]
        subgraph AppSubnets [Private Application Subnets]
            API[FastAPI Gateway ECS Tasks]
            Worker[Celery Worker ECS Tasks]
        end

        subgraph DataSubnets [Private Data Subnets (No Public IP)]
            DevDB[(RDS: fashx-pg-dev<br/>DB: fashx_dev<br/>Single-AZ, 7d retention)]
            StagingDB[(RDS: fashx-pg-staging<br/>DB: fashx_staging<br/>Single-AZ, 14d retention)]
            ProdDB[(RDS: fashx-pg-prod<br/>DB: fashx_prod<br/>Multi-AZ, 30d retention)]
        end
    end

    API -->|TLS Port 5432 / IAM Secrets| StagingDB
    Worker -->|TLS Port 5432 / IAM Secrets| StagingDB
```

## 2. Environment Instance Inventory

| Environment | DB Instance Identifier | Database Name | Compute Class | Storage | Availability | Backup Retention |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Development** | `fashx-pg-dev` | `fashx_dev` | `db.t4g.micro` | 20 GB gp3 | Single-AZ | 7 days |
| **Staging** | `fashx-pg-staging` | `fashx_staging` | `db.t4g.small` | 20 GB gp3 | Single-AZ | 14 days |
| **Production** | `fashx-pg-prod` | `fashx_prod` | `db.r6g.large` | 100 GB gp3 | Multi-AZ | 30 days |

## 3. Database Engine & Extensions

- **Engine Version**: PostgreSQL 16.2.
- **Extensions**:
  - `vector` (`pgvector`): Native vector embeddings indexing for catalog product image search and shopper visual similarity matching.
  - Parameter group `shared_preload_libraries = "vector"`.
- **Encryption & Transport Security**:
  - Storage encrypted at rest using AWS KMS (`aws/rds` managed key or customer-managed CMK).
  - Transit encryption enforced via parameter group `rds.force_ssl = 1`. Application connections must provide AWS RDS root CA certificates.

## 4. Connection Pooling & Resource Governance

- **Application Pool**: SQLAlchemy async engine (`asyncpg`) utilizing `QueuePool`:
  - Persistent pool size: 10 connections per container.
  - Max overflow: 5 connections.
  - Pool timeout: 30 seconds.
  - Pool pre-ping: `True` (verifies connection vitality prior to checkout).
  - Pool recycle: 1800 seconds (prevents stale TCP connections).
- **Telemetry**: Real-time pool metrics (`DbPoolSize`, `DbPoolCheckedIn`, `DbPoolCheckedOut`, `DbPoolOverflow`) emitted via CloudWatch Embedded Metric Format (EMF) to `FashX/Database`.

## 5. Migration Execution Strategy

- Schema changes are managed exclusively through Alembic.
- Migrations never execute at API container boot. They are run as an isolated, one-off ECS Fargate task prior to service deployment (`alembic upgrade head`).
- The pipeline enforces single migration heads and backward-compatible expand/contract patterns.
