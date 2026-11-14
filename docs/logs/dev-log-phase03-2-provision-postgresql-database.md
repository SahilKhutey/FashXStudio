> **Development log. Contains no real-world measurements or simulated evidence. Pre-pilot status maintained per AGENTS.md.**

# Dev Log: Phase 03.2 — Production Infrastructure and Backend Integration: Provision PostgreSQL Database

**Branch**: `recovery/rc13.1-governance-correction`
**Milestone Scope**: Phase 03 — Production Infrastructure and Backend Integration (Section 3.2: Provision PostgreSQL Database)
**Date**: November 12, 2026
**Status**: Completed & Verified Locally

---

## 1. Context & Architectural Decisions

Phase 03.1 established the environment definition and security invariants. Phase 03.2 establishes the persistent relational and vector database architecture for FashXStudio:

### Key Technical Decisions
1. **Managed Service**: **AWS RDS for PostgreSQL 16**.
2. **Target Region**: **`ap-south-1` (Mumbai, India)** for low latency and data localization.
3. **Database Topology**:
   - Production: Dedicated Multi-AZ instance (`fashx-pg-prod`, `db.t4g.medium`/`db.r6g.large`) with synchronous physical standby and continuous WAL archiving (30-day PITR).
   - Staging: Dedicated Single-AZ instance (`fashx-pg-staging`, `db.t4g.small`, 14-day backup retention).
   - Development: Dedicated Single-AZ instance (`fashx-pg-dev`, `db.t4g.micro`, 7-day backup retention).
   - Complete physical and network isolation across all three environments with non-overlapping security groups and credentials.
4. **Vector Embeddings**: Native `pgvector` v0.7.0+ extension on PostgreSQL 16, integrated with 512-dimensional garment and shopper style vectors via `Vector512` model mappings.
5. **Least Privilege Role Segregation**:
   - `fashx_*_app`: Granted strictly DML rights (`SELECT`, `INSERT`, `UPDATE`, `DELETE`). Explicitly denied DDL commands (`CREATE`, `DROP`, `ALTER`).
   - `fashx_*_migrator`: Schema owner executing Alembic migrations (`CREATE`, `ALTER`, `DROP`).

---

## 2. Technical Implementation Highlights

### A. Connection Pooling Optimization (`backend/fashx/core/settings.py` & `database.py`)
- Added configurable connection pool parameters to `Settings`:
  - `db_pool_size`: Default 5 (configurable per environment).
  - `db_max_overflow`: Default 5.
  - `db_pool_timeout`: Default 20 seconds.
- Enhanced `get_engine()` in `backend/fashx/core/database.py` to conditionally inject pooling parameters for PostgreSQL connections while maintaining compatibility with SQLite in unit testing.

### B. Terraform Infrastructure as Code (`infra/aws/rds/`)
- Codified complete three-instance RDS infrastructure in `infra/aws/rds/`:
  - `versions.tf`: Pinned Terraform `>= 1.10.0` and AWS provider `>= 5.80, < 7.0` with S3 remote state backend and state locking.
  - `variables.tf`: Parameterized VPC ID, private subnet IDs, app security groups, and instance classes.
  - `main.tf`: Created subnet group, custom parameter group (`rds.force_ssl=1`), 3 environment-specific security groups with strict ingress from app tiers only, and 3 RDS DB instances with Secrets Manager master password management.
  - `outputs.tf`: Exported private endpoints, security group IDs, and master secret ARNs.
  - `terraform.tfvars.example`: Example variables file for deployment engineers.

### C. Operational Database Scripts (`scripts/db/`)
- `scripts/db/bootstrap_rds_roles.sh`: Automatic role bootstrap script creating Secrets Manager secrets and configuring least-privilege PostgreSQL roles for dev, staging, and prod.
- `scripts/db/verify_rds.sh`: AWS CLI instance audit tool querying instance status, encryption, retention, and endpoints.
- `scripts/db/backup_postgres.sh`: Custom-format logical database dump with SHA-256 checksum generation and `pg_restore --list` pre-validation.
- `scripts/db/benchmark_postgres.py`: High-concurrency connection establishment and query latency benchmark using asyncpg.
- `scripts/db/verify_database.sh`: Automated preflight script inspecting database identity, PostgreSQL version, TLS status, pgvector extension, table counts, and Alembic revision.

### D. Infrastructure Test Suites (`tests/infrastructure/`)
- `tests/infrastructure/test_database_environment_isolation.py`: Target URL comparison, port distinction, and RDS endpoint distinctness assertions.
- `tests/infrastructure/test_database_permissions.py`: Testing DML vs DDL separation and verifying that application queries reject prohibited DDL keywords (`DROP TABLE`, `CREATE TABLE`).
- `tests/infrastructure/test_database_persistence.py`: Testing data persistence across independent engine cycles and transaction rollback safety.

### E. Architectural Documentation (`docs/infrastructure/`)
- Published `AWS_RDS_ARCHITECTURE.md` alongside the 10 database specifications and backup inventory register.
