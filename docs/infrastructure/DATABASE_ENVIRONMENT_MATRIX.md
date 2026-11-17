# Database Environment Specification Matrix

This document defines the database tier configuration across all FashXStudio operating environments.

| Property | Local Workstation | Development | Staging (RC) | Production |
| :--- | :--- | :--- | :--- | :--- |
| **Hosting Model** | Docker / Local Workstation | AWS RDS (Single-AZ) | AWS RDS (Non-prod cluster) | AWS RDS (Multi-AZ Dedicated) |
| **Instance Identifier** | `fashx-local-postgres` | `fashx-pg-nonprod` | `fashx-pg-nonprod` | `fashx-pg-prod` |
| **Instance Class / SKU** | Local container | `db.t4g.micro` (2 vCPU, 1 GB) | `db.t4g.small` (2 vCPU, 2 GB) | `db.r6g.large` (2 vCPU, 16 GB Memory-Optimized) |
| **Database Name** | `fashion` (test: `fashion_test`) | `fashx_dev` | `fashx_staging` | `fashx_prod` |
| **Application Runtime Role** | `fashion` | `fashx_dev_app` | `fashx_staging_app` | `fashx_prod_app` |
| **Migration Role** | `fashion` | `fashx_dev_migrator` | `fashx_staging_migrator` | `fashx_prod_migrator` |
| **Network Visibility** | `127.0.0.1` only | Private VPC Subnet (No Public IP) | Private VPC Subnet (No Public IP) | Isolated Private Database Subnet |
| **TLS / SSL Invariant** | Optional (Local dev) | Required (`ssl=require`) | Required (`ssl=require`) | Enforced (`rds.force_ssl=1`, `ssl=verify-full`) |
| **`pgvector` Extension** | Enabled (`vector` 0.7+) | Enabled (`vector` 0.7+) | Enabled (`vector` 0.7+) | Enabled (`vector` 0.7+) |
| **Connection Pooling** | SQLAlchemy async pool (5+5) | SQLAlchemy pool (5+5) | SQLAlchemy pool (5+5) | SQLAlchemy pool (10+10) + RDS Proxy |
| **Max Instance Connections**| 100 | 100 | 150 | 1,000 |
| **Automated Backups** | None (Local volumes) | Daily snapshot (7-day retention)| Daily snapshot (7-day retention) | Daily snapshot + Continuous WAL (35 days) |
| **Point-In-Time Recovery** | Not applicable | Not active | 7-day window | 35-day continuous window |
| **Restore Drill Cadence** | On developer demand | Quarterly automated script | Quarterly automated script | Monthly formal rehearsal |
| **Customer Data Scope** | 100% Synthetic mock data | Synthetic test fixtures | Sanitized pre-pilot test fixtures| Authorized real shopper/merchant data |

---

## Environment Separation Invariants

1. **Non-Overlapping Access**: Credentials for `fashx_dev_app` and `fashx_staging_app` cannot connect to `fashx_prod`. AWS Security Groups physically deny connections from the Development or Staging ECS clusters to the Production RDS instance.
2. **Migration Privilege Separation**: `fashx_*_app` roles are strictly restricted to DML operations (`SELECT`, `INSERT`, `UPDATE`, `DELETE`). Only migration tasks executing under `fashx_*_migrator` possess DDL rights to modify tables, sequences, or indexes.
